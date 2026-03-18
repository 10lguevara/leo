#!/usr/bin/env python3
"""A simple text-based travel game inspired by Oregon Trail with a Chutes & Ladders theme.

You and your party must travel from Start to Finish along a linear track of spaces.
Each turn you roll a die to move forward. Some spaces are ladders (move you forward)
and some are chutes (send you backward). Along the way you can rest, hunt, and
manage supplies. The goal is to reach the end of the trail while keeping your
party alive.

This is intentionally simple to keep the gameplay fast and the code easy to read.
"""

import random
import sys
import time

BOARD_LENGTH = 31

# Chutes (negative) and ladders (positive) mapped by position
TRACK_FEATURES = {
    3: 8,   # ladder: go from 3 to 11
    6: -5,  # chute: go from 6 to 1
    9: 7,   # ladder: go from 9 to 16
    14: -10, # chute: go from 14 to 4
    17: 5,  # ladder: go from 17 to 22
    18: -4, # chute: go from 18 to 14
    21: -11, # chute: go from 21 to 10
    23: -6, # chute: go from 23 to 17
    24: 6,  # ladder: go from 24 to 30
    26: -8, # chute: go from 26 to 18
    # Space 30 is a false finish that rewinds you to start.
}

INITIAL_SUPPLIES = 10
INITIAL_HEALTH = 10

def slow_print(text: str, delay: float = 0.02):
    """Print text with a small delay for a more dramatic effect."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def roll_die(sides: int = 6) -> int:
    return random.randint(1, sides)


def calculate_move(roll: int, health: int, supplies: int) -> tuple[int, str]:
    """Adjust movement based on health and supplies.

    Higher health can speed you up, while low health or low supplies slows you down.
    """
    move = roll
    notes = []

    if health >= 9:
        move += 1
        notes.append("you feel strong")
    elif health <= 3:
        move -= 1
        notes.append("you're weak")

    if supplies >= 12:
        move += 1
        notes.append("your wagon is well-stocked")
    elif supplies <= 2:
        move -= 1
        notes.append("you are near starvation")

    move = max(1, move)
    note = ", ".join(notes) if notes else ""
    return move, note


def describe_position(pos: int) -> str:
    if pos in TRACK_FEATURES:
        delta = TRACK_FEATURES[pos]
        if delta > 0:
            return f"You found a ladder! It will move you ahead {delta} spaces."
        else:
            return f"Oh no — a chute! It will send you back {abs(delta)} spaces."
    return "The trail is quiet here."


def apply_feature(position: int) -> int:
    if position in TRACK_FEATURES:
        return max(0, position + TRACK_FEATURES[position])
    return position


def print_status(turn: int, position: int, health: int, supplies: int):
    display_pos = min(position, 30)
    slow_print(f"\n=== Turn {turn} ===")
    slow_print(f"Position: {display_pos}/30  |  Health: {health}  |  Supplies: {supplies}")


def get_choice() -> tuple[str, str]:
    choices = "[R]oll  [H]unt  [E]at  [Q]uit"
    slow_print(choices)
    raw = input("> ").strip()
    return raw, raw.lower()


def do_hunt(supplies: int, health: int) -> tuple[int, int]:
    slow_print("You go hunting for supplies...")
    outcome = random.random()
    if outcome < 0.5:
        gained = random.randint(1, 4)
        supplies += gained
        slow_print(f"Success! You brought back {gained} supplies.")
    elif outcome < 0.8:
        lost = random.randint(1, 2)
        health -= lost
        slow_print(f"You got hurt while hunting and lost {lost} health.")
    else:
        slow_print("The hunt came up empty.")
    return supplies, health


def do_eat(supplies: int, health: int) -> tuple[int, int]:
    if supplies <= 0:
        slow_print("You have no supplies to eat. Try hunting.")
        return supplies, health
    slow_print("You eat a meal and regain some strength.")
    supplies -= 1
    health = min(10, health + 2)
    return supplies, health


def encounter_event(position: int, health: int, supplies: int) -> tuple[int, int, int]:
    # Chance for random events at each new position
    # Supplies and health affect outcomes.
    if supplies <= 2 and random.random() < 0.25:
        health -= 1
        slow_print("Hunger bites. You lose 1 health due to a lack of supplies.")

    # Random fatal chutes: several different hideous traps can instantly end the game.
    fatal_roll = random.random()
    if fatal_roll < 0.03:
        health = 0
        slow_print("A hidden chute opens beneath you! You fall too far to recover.")
        return position, health, supplies
    if fatal_roll < 0.06:
        health = 0
        slow_print("The ground splits and you tumble into a dark abyss.")
        return position, health, supplies
    if fatal_roll < 0.09:
        health = 0
        slow_print("A pack of unseen creatures drags you down a chute into nowhere.")
        return position, health, supplies

    # Random hidden win: sometimes you stumble on a secret shortcut to the end.
    if random.random() < 0.03:
        position = BOARD_LENGTH
        slow_print("You discover a secret path that leads straight to the finish!")
        return position, health, supplies

    # Random weird person encounter: they ask for a potion (supply) in exchange for a boon.
    if random.random() < 0.1:
        slow_print("A strange traveler appears and offers you a mysterious potion in exchange for a supply.")
        if supplies > 0:
            slow_print("Do you give them 1 supply? (y/n)")
            answer = input("> ").strip().lower()
            if answer in ("y", "yes"):
                supplies -= 1
                health = min(10, health + 3)
                position = min(BOARD_LENGTH, position + 1)
                slow_print("The potion surges through you! +3 health and you stumble forward 1 space.")
            else:
                slow_print("The traveler shrugs and fades away, leaving you wondering what might have been.")
        else:
            slow_print("You have no supplies to trade, and the traveler disappears into the mist.")

    event_roll = random.random()
    if event_roll < 0.15:
        lost = random.randint(1, 3)
        health -= lost
        slow_print(f"A storm hits! You lose {lost} health.")
    elif event_roll < 0.3:
        found = random.randint(1, 3)
        supplies += found
        slow_print(f"You found a hidden cache and gain {found} supplies.")
    elif event_roll < 0.4:
        health += 1
        slow_print("A friendly traveler shares some advice. You feel better (+1 health).")
    elif supplies >= 12 and event_roll < 0.5:
        # High supplies give you the chance to rig up a shortcut
        bonus = random.randint(1, 2)
        position += bonus
        slow_print(f"Your well-stocked wagon helps you blaze ahead {bonus} extra spaces.")

    return position, health, supplies


def game_over(position: int, health: int, supplies: int) -> bool:
    if health <= 0:
        slow_print("Your party has succumbed to the hardships of the trail.")
        return True
    if supplies <= -2:
        slow_print("You ran completely out of supplies and can't continue.")
        return True
    if position >= BOARD_LENGTH:
        slow_print("\n🎉 Congratulations! You reached the end of the trail! 🎉")
        return True
    return False


def print_board(position: int):
    # Simple textual board representation with player marker
    board = []
    for i in range(BOARD_LENGTH + 1):
        if i == position:
            board.append("👣")
        elif i in TRACK_FEATURES:
            delta = TRACK_FEATURES[i]
            board.append("🔼" if delta > 0 else "🔽")
        else:
            board.append("·")
    slow_print("".join(board))


def main():
    random.seed()
    position = 0
    health = INITIAL_HEALTH
    supplies = INITIAL_SUPPLIES

    slow_print("Welcome to Oregon Trail: Chutes & Ladders Edition!\n")
    slow_print("You must travel from Start (0) to Finish (30) while managing your health and supplies.")
    slow_print("Watch out for chutes (🔽) and ladders (🔼) along the trail.\n")

    turn = 1
    while True:
        print_status(turn, position, health, supplies)
        print_board(position)

        choice_raw, choice = get_choice()

        # Secret code: enter "Leo" to trigger a sudden win or death.
        if choice == "leo":
            if random.random() < 0.5:
                position = BOARD_LENGTH
                slow_print("A secret force answers your call. You are instantly teleported to the end!")
            else:
                health = 0
                slow_print("A shadowy curse consumes you the moment you say the name. You die instantly.")
            break

        if choice in ("q", "quit", "exit"):
            slow_print("Thanks for playing! Goodbye.")
            break

        if choice in ("h", "hunt"):
            supplies, health = do_hunt(supplies, health)
        elif choice in ("e", "eat"):
            supplies, health = do_eat(supplies, health)
        elif choice in ("r", "roll"):
            roll = roll_die()
            move, note = calculate_move(roll, health, supplies)
            slow_print(f"You rolled a {roll} and move {move} spaces." + (f" ({note})" if note else ""))
            position += move
            if position > BOARD_LENGTH:
                position = BOARD_LENGTH

            slow_print(describe_position(position))
            new_position = apply_feature(position)
            if new_position != position:
                slow_print(f"You move to space {new_position}.")
                position = new_position

            # Monster ambush at space 25
            if position == 25:
                health = 0
                slow_print("A monstrous creature springs from the shadows at 25 and devours you!")
                # skip further events; game_over will handle the end
            elif position == 30:
                slow_print("🎉 You reached space 30! It feels like a win… 🎉")
                time.sleep(5)
                slow_print("But suddenly the world blurs. You wake up from your illusion.")
                slow_print("The trail breaks apart and you tumble back to the start. You must try again.")
                position = 0
                supplies = max(0, supplies - 2)
                health = max(1, health - 1)
            elif position == 29:
                health = 0
                slow_print("The door just before the finish collapses and crushes you!")
            elif position == BOARD_LENGTH:
                slow_print("You find the true finish line at space 31! This time you have really won.")
            else:
                position, health, supplies = encounter_event(position, health, supplies)
        else:
            slow_print("I didn't understand that. Please choose R, H, E, or Q.")
            continue

        # Low supplies gradually sap your health each turn if you can't eat.
        if supplies <= 0:
            health -= 1
            slow_print("You have no supplies left and lose 1 health from hunger.")

        if game_over(position, health, supplies):
            break

        turn += 1

    slow_print("Game over. Thanks for playing!")


if __name__ == "__main__":
    main()
