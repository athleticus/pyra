#!/usr/bin/python
import sys
import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))

if len(sys.argv) < 2:
    print "Requires a file."
    exit(1)

name = sys.argv[1]

if not name.endswith('.outraw'):
    name += '.outraw'

output = []

EMPTY = "----/---"

with open(name, 'rU') as fd:
    for line in fd:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        elif line.startswith('R'):
            # Round winner
            winners = " ".join(list(line[1:-1]))
            output.append("Round winner(s) holding {}: {}".format(line[-1], winners))

        elif line.startswith('W'):
            # Game winner
            winners = " ".join(list(line[1:]))
            output.append("Winner(s): {}".format(winners))

        else:
            # Move
            line2 = list(EMPTY)
            for i, char in enumerate(line):
                line2[i] = char

            line = line2

            player = line[0]
            play = line[1]
            target = line[2]
            guess = line[3]
            dropper = line[5]
            dropped = line[6]
            dead = line[7]            

            out = "Player {} discarded {}".format(player, play)
            if target != '-':
                out += " aimed at {}".format(target)
                if guess != '-':
                    out += " guessing {}".format(guess)
            out += '.'

            if dropper != '-':
                out += " This forced {} to discard {}.".format(dropper, dropped)

            if dead != '-':
                out += " {} was out.".format(dead)


            output.append(out)

output = "\n".join(output) + '\n'

with open(name.replace('.outraw', '.out'), 'w') as fd:
    fd.write(output)
