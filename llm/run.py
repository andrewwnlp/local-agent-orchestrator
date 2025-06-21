import argparse
from datasets import load_from_disk, load_dataset
from tqdm import tqdm
from local_workflow import environment
from local_workflow.agent import BaseAgent
from local_workflow.local_logging.utils import setup_logs, configure_logging
from external_tools import add, subtract, multiply, divide, verify
from functools import partial
import inspect

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, help="location of config file")
    parser.add_argument(
        '--log-level',
        default='TRACE',
        choices=['DEBUG', 'TRACE', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)'
    )
    args = parser.parse_args()

    configure_logging(level=args.log_level)
    config, results_path = setup_logs(args.config_file)

    ds = load_dataset(config['data']['dataset_path'], config['data']['subset'])[config['data']['split']]
    pbar = tqdm(ds)
    static_tools = [
        add,
        subtract,
        multiply,
        divide,
    ]
    env_classes = {
        name: cls
        for name, cls in inspect.getmembers(environment, inspect.isclass)
        if cls.__module__ == environment.__name__
    }

    success = 0
    for count, record in enumerate(pbar):
        non_static_tools = [partial(verify, solution=record['answer'])]
        tools = static_tools + non_static_tools
        game = env_classes[config['tool']['handler']](config, setup_data=record, tools=tools, results_path=results_path)
        agent = BaseAgent(config['generation'], config['server'])
        game.play(agent)
        success += game.correctness
        pbar.set_description(f"success: {success}, count: {count+1}, accuracy: {success / (count+1)}")

