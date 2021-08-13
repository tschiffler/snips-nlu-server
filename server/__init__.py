import json
import shutil
from os import makedirs, path, listdir
from typing import Any
from flask.helpers import make_response
from snips_nlu import SnipsNLUEngine
from flask import Flask, request
from execjs import get
from werkzeug.exceptions import HTTPException
from server.exceptions import MissingParameterException, WrongFormatException

app = Flask(__name__)
node = get('Node')

node_env = node.compile('''
    const { JovoModelSnips } = require('jovo-model-snips');
    
    function convert(locale, model) {
      const snipsModelFiles = JovoModelSnips.fromJovoModel(model, locale);
      
      return snipsModelFiles[0].content;
    }
''')

@app.before_request
def check_request_type():
    ''' Checks if the current request MIME type is set to application/json '''
    if request.method == 'POST' and not request.is_json:
        raise WrongFormatException('Request body must be JSON.')

@app.route('/engine/train', methods=['POST'])
async def train_generic_engine():
    ''' Creates, trains and persists a Snips NLU Engine '''
    train_and_persist_engine()
    return '', 201

@app.route('/engine/train/dynamic-entities', methods=['POST'])
async def train_dynamic_entities():
    ''' Creates, trains and persists a Snips NLU Engine for dynamic entities '''
    entity: str = get_query_parameter('entity')
    session_id: str = get_query_parameter('session_id')

    engine_path: str = path.join('dynamic_entities', session_id, 'engine_{0}'.format(entity))
    train_and_persist_engine(engine_path)
    return '', 201

@app.route('/engine/parse', methods=['POST'])
async def parse_message():
    ''' Loads a Snips NLU Engine and parses a message through it '''
    engine_id: str = get_query_parameter('engine_id')
    session_id: str = get_query_parameter('session_id')

    engine_directory: str = path.join('.engine', engine_id)
    # Parse through every engine trained on dynamic entities.
    # If a result is found, return it, otherwise fall back to the generic engine.
    dynamic_engine_path: str = path.join('.engine', engine_id, 'dynamic_entities', session_id)
    if path.exists(dynamic_engine_path):
        for directory in listdir(dynamic_engine_path):
            result = parse_from_engine(path.join(dynamic_engine_path, directory))
            if result['intent']['intentName'] is not None:
                return result, 200
            
    result = parse_from_engine(path.join(engine_directory, 'engine'))
    return result, 200

@app.errorhandler(HTTPException)
def handle_exception(exception):
    response = getattr(exception, 'get_response', make_response)()
    response.data = json.dumps({
        'code': exception.code,
        'description': exception.description,
        'name': type(exception).__name__,
    })
    response.content_type = 'application/json'
    return response, exception.code

def train_and_persist_engine(engine_path_portion: str = 'engine'):
    engine: SnipsNLUEngine = SnipsNLUEngine()
    locale: str = get_query_parameter('locale')
    bot_id: str = get_query_parameter('engine_id')

    # TODO: Catch errors?
    snipsModel = node_env.call('convert', locale, request.json)
    engine.fit(snipsModel)

    engine_path: str = path.join('.engine', bot_id, engine_path_portion)

    # Create directory if it doesn't exist yet
    engine_directory: str = path.dirname(engine_path)

    if not path.exists(engine_directory):
        makedirs(engine_directory)

    # If the engine already exists, delete it first
    if path.exists(engine_path):
        shutil.rmtree(engine_path)

    engine.persist(engine_path)

def parse_from_engine(engine_path: str) -> Any:
    engine: SnipsNLUEngine = SnipsNLUEngine.from_path(engine_path)
    request_json: Any = request.get_json()
    result = engine.parse(request_json['text'])
    return result

def get_query_parameter(key: str) -> str:
    ''' Checks if a request query parameter is provided and returns it '''
    parameter = request.args.get(key)
    if not parameter:
        raise MissingParameterException('Missing parameter key: {key}'.format(key=key))

    return parameter
