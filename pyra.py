#! /usr/bin/env python3
__author__ = 'ben'

import subprocess, os, difflib, shlex, argparse

from lib.termcolor import colored
from lib.colorama import init

init()

class TestRunner(object):

    # Default values for settings
    DEFAULTS = {
        'resultsDir': 'testres/',
        'assetsDir': 'assets/',
        'execDir': '.',
        'timeout': 2,
        'details': False,
        'fullPath': False
    }

    # Types of output from the script
    OUTPUTS = ['out', 'err']

    def _log(self, message, show = True):
        if show:
            print(message)

    def _printDetail(self, message):
        self._log(message, show = self._config['details'])

    def _printNoDetail(self, message):
        self._log(message, show = not self._config['details'])


    def __init__(self, tests, config=None):
        # Fill configuration options in with defaults
        self._config = dict(self.DEFAULTS, **(config or {}))

        # Parse tests
        self._parse_tests(tests)

    def _parse_tests(self, tests):
        res = []

        for testLine in tests.split('\n'):
            testLine = testLine.strip()

            if not testLine or testLine.startswith('#'):
                continue

            test = testLine.split('|')

            test = {
                'exec': test[0],
                'code': int(test[1]),
                'in': test[2],
                'out': test[3],
                'err': test[4],
                'args': test[7],
                'name': test[8]
            }

            res.append(test)

        self._tests = res

    def _color_diff(self, diff):
        colours = {
            '+': 'cyan',
            '-': 'red',
            '?': 'yellow',
            ' ': 'white',
            '@': 'yellow'
        }

        defaultColour = 'white'

        return [colored(line, colours.get(line[0], defaultColour)) for line in diff]


    def run_tests(self, indices=None):
        res = []

        if not os.path.exists(self._config['resultsDir']):
            os.makedirs(self._config['resultsDir'])

        tests = [(i + 1, test) for i, test in enumerate(self._tests) if indices is None or i + 1 in indices]

        cmdColour = 'white'

        for i, test in tests:
            opts = test.copy()

            testNum = i

            opts['exec'] = os.path.join(self._config['execDir'], opts['exec'])
            opts['actual_out'] = os.path.join(self._config['resultsDir'], 'test.{}.out'.format(testNum))
            opts['actual_err'] = os.path.join(self._config['resultsDir'], 'test.{}.err'.format(testNum))
            opts['supplied_in'] = os.path.join(self._config['assetsDir'], opts['in'])
            opts['expected_out'] = os.path.join(self._config['assetsDir'], opts['out'])
            opts['expected_err'] = os.path.join(self._config['assetsDir'], opts['err'])

            for key in ['exec', 'actual_out', 'actual_err', 'supplied_in', 'expected_out', 'expected_err']:
                opts[key] = os.path.normpath(opts[key])
                opts[key] = opts[key].replace(self._config['execDir'], '.')
                opts[key + '_sh'] = opts[key] if config['fullPath'] else shlex.quote(opts[key])

            cmd = '{exec_sh} {args} < {supplied_in_sh} 1> {actual_out_sh} 2> {actual_err_sh}'.format(**opts)

            self._printDetail("Test {}: \n\t{}".format(testNum, colored(cmd, cmdColour)))

            success = True
            timedOut = False

            proc = subprocess.Popen(cmd, shell = True)
            try:
                proc.communicate(timeout=self._config['timeout'])
                code = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                timedOut = True
                self._log("Execution timed out after {} seconds...".format(self._config['timeout']))
                success = False

            if success:
                # Check code
                if code != opts['code']:
                    self._printDetail("Failed with wrong exit code; got {} but expecting {}".format(code, opts['code']))
                    success = False

                # Check stdout & stderr
                for output in self.OUTPUTS:

                    expectedFile = opts['expected_' + output]
                    actualFile = opts['actual_' + output]

                    data = {
                        'expected': opts['expected_' + output + '_sh'],
                        'actual': opts['actual_' + output + '_sh']
                    }

                    diffCmd = "diff {expected} {actual}".format(**data)

                    with open(expectedFile, 'rU') as fd:
                        expected = fd.readlines()

                    with open(actualFile, 'rU') as fd:
                        actual = fd.readlines()

                    diff = difflib.unified_diff(expected, actual, fromfile = '{} (expected)'.format(expectedFile), tofile = '{} (actual)'.format(actualFile))
                    diff = list(diff)

                    if bool(len(diff)):
                        self._printDetail("{} differs:\n\t{}".format(output, colored(diffCmd, cmdColour)))
                        self._printDetail('-' * 80)
                        self._printDetail("".join(self._color_diff(diff)))
                        success = False
                        self._printDetail('-' * 80)

            res.append(success)

            outcome = colored("PASSED", 'green') if success else colored("FAILED", 'red')

            self._printDetail(outcome)

            self._printNoDetail(colored("Test {} {}".format(testNum, outcome), 'green' if success else 'red'))

            self._printDetail("=" * 80)

        self._log("Passed {}/{} tests!".format(sum(res), len(tests)))

TESTS = """
# exec|retval|input|expected_output|expected_err|||args

#Argument number
./player|1|empty|dash|incorrect_args.out||||Incorrect args 0
./player|1|empty|dash|incorrect_args.out|||x|Incorrect args 1
./player|1|empty|dash|incorrect_args.out|||x x x|Incorrect args 3
./player|1|empty|dash|incorrect_args.out|||x x x x|Incorrect args 4

#Player count
./player|2|empty|dash|invalid_player_count.out|||-1 A|Player count -1
./player|2|empty|dash|invalid_player_count.out|||0 A|Player count 0
./player|2|empty|dash|invalid_player_count.out|||1 A|Player count 1
./player|3|empty|dash|invalid_player_id.out|||2 x|Player count 2
./player|3|empty|dash|invalid_player_id.out|||3 x|Player count 3
./player|3|empty|dash|invalid_player_id.out|||4 x|Player count 4
./player|2|empty|dash|invalid_player_count.out|||5 A|Player count 5
./player|2|empty|dash|invalid_player_count.out|||3biscuit A|Player count 3biscuit
./player|2|empty|dash|invalid_player_count.out|||3b3 A|Player count 3b3

#Player ID
./player|3|empty|dash|invalid_player_id.out|||3 a|Player ID a
./player|3|empty|dash|invalid_player_id.out|||3 b|Player ID b
./player|3|empty|dash|invalid_player_id.out|||3 c|Player ID c
./player|3|empty|dash|invalid_player_id.out|||3 d|Player ID d
./player|3|empty|dash|invalid_player_id.out|||3 AA|Player ID AA
./player|3|empty|dash|invalid_player_id.out|||3 BBBB|Player ID BBBB
./player|3|empty|dash|invalid_player_id.out|||3 D|Player ID D
./player|3|empty|dash|invalid_player_id.out|||2 C|Player ID C
./player|4|empty|dash|loss_of_hub.out|||3 A|Player ID A
./player|4|empty|dash|loss_of_hub.out|||3 B|Player ID B
./player|4|empty|dash|loss_of_hub.out|||3 C|Player ID C
./player|4|empty|dash|loss_of_hub.out|||4 D|Player ID D

#Gameover
./player|0|gameover.in|dash|gameover.out|||3 A|Gameover
./player|5|gameove.in|dash|gameove.out|||3 A|Gameove
./player|5|gameover_no_nl.in|dash|gameover_no_nl.out|||3 A|Gameover no new line
./player|5|gameover_space.in|dash|gameover_space.out|||3 A|Gameover<space>

#New round
./player|0|new_round.in|dash|new_round.out|||4 B|New Round
./player|5|new_round_card_0.in|dash|new_round_card_0.out|||4 B|New round card 0
./player|5|new_round_card_x.in|dash|new_round_card_x.out|||4 B|New round card x
./player|5|new_round_card_9.in|dash|new_round_card_9.out|||4 B|New round card 9
./player|5|new_round_card_111.in|dash|new_round_card_111.out|||4 B|New round card 111
./player|5|new_round_no_card.in|dash|new_round_no_card.out|||4 B|New round card no card
"""



if __name__ == '__main__':
    config = {
        'execDir': os.path.normpath(os.getcwd()),
        'resultsDir': os.path.normpath(os.path.join(os.getcwd(), './testres')),
        'assetsDir': os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets/'))
    }

    parser = argparse.ArgumentParser("Run tests.")
    parser.add_argument('-d', dest='details', action='store_const', default=False, const=True, help='Show detailed output for each test.')
    parser.add_argument('-t', dest='timeout', default=5, help='Set the time limit, in seconds, for each test to run.')
    parser.add_argument('--full-path', dest='fullPath', action='store_const', default=False, const=True, help='Use the full path for all files.')
    parser.add_argument('tests', type=int, nargs='?', default=None, help="The specific test to run.")

    args = vars(parser.parse_args())
    config.update(args)

    indices = None if config['tests'] is None else [config['tests']]

    TestRunner(TESTS, config).run_tests(indices=indices)
