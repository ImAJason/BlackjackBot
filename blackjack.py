import dbmanage as db
import random
import asyncio
from decimal import *


class Card:

    def __init__(self, suit, rank, value):

        self.suit = suit
        self.value = value
        self.rank = rank

    def get_suit(self):

        return self.suit

    def get_value(self):

        return self.value

    def get_rank(self):

        return self.rank

    def __str__(self):

        return "| " + self.rank + " " + self.suit + " |"


class Deck:

    ranks = [('A', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7), ('8', 8), ('9', 9), ('10', 10),
             ('J', 10), ('Q', 10), ('K', 10)]
    #suits = ['Spades', 'Diamonds', 'Hearts', 'Clubs']
    suits = ['\u2664', '\u2662', '\u2661', '\u2667']

    cards = []
    dealtIndex = 0

    def __init__(self):
        pass

    def populate(self):

        for s in self.suits:
            for r in self.ranks:
                suit = s
                rank = r[0]
                value = r[1]

                c = Card(suit, rank, value)
                self.cards.append(c)

    def shuffle(self):

        for i in range(len(self.cards)-1, -1, -1):
            r = random.randint(0, i)
            self.cards[i], self.cards[r] = self.cards[r], self.cards[i]

    def deal(self):

        card = self.cards[self.dealtIndex]
        self.dealtIndex += 1
        return card

    def get_cards(self):

        return self.cards


class Hand:

    def __init__(self, bet=0):

        self.cards = []
        self.scores = []
        self.valid_moves = []
        self.bet = bet
        self.split_status = False

    def add(self, card):

        self.cards.append(card)
        self.update_scores()
        self.update_valid_moves()

    def update_valid_moves(self):

        valid = ['stay', 'quit', 'q']

        for score in self.scores:
            if score > 21:
                self.valid_moves = 'bust'
                return
            elif score == 21:
                self.valid_moves = 'blackjack'
                return

        valid.append('hit')

        if len(self.cards) == 2:
            if not self.split_status:
                valid.append('double')

        if len(self.cards) == 2:
            #if self.cards[0].rank == self.cards[1].rank:
            valid.append('split')

        self.valid_moves = valid

    def update_scores(self):

        s = [0]
        has_ace = False

        for card in self.cards:
            s[0] += card.value
            if card.rank == 'A':
                has_ace = True

        if has_ace and s[0] < 12:
            s.append(s[0]+10)

        self.scores = s


class Player:

    def __init__(self, server_id, player_id, player_name, bot=None):

        self.player_id = player_id
        self.player_name = player_name
        self.bot = bot
        self.money = db.get_money(server_id, player_id)

    async def make_move(self, ctx, hand):

        #move = (input("Move? ")).lower()
        bot_ask_move = await self.bot.say("Move? ")
        await asyncio.sleep(1.0)

        move = await self.bot.wait_for_message(timeout=20)

        if move.content.lower().startswith("t."):
            return

        if move.content.lower() == 'q' or move.content.lower() == 'quit':
            move = -1
            return move

        while True:

            move = move.content.lower()

            if ctx.message.author.id != self.player_id:
                await self.bot.say("Only **{0}** can decide a move".format(self.player_name))
                await asyncio.sleep(1.0)
                move = await self.bot.wait_for_message(timeout=15)

            if move not in hand.valid_moves:
                await self.bot.say("Invalid move. Move? ")
                await asyncio.sleep(1.0)
                move = await self.bot.wait_for_message(timeout=15)

            elif (move == 'double') and (self.money < hand.bet):
                await self.bot.say("Not enough to double. Move? ")
                await asyncio.sleep(1.0)
                move = await self.bot.wait_for_message(timeout=15)

            elif (move == 'split') and (self.money < hand.bet):
                await self.bot.say("Not enough to split. Move? ")
                await asyncio.sleep(1.0)
                move = await self.bot.wait_for_message(timeout=15)

            else:
                break

        await asyncio.sleep(0.5)
        await self.bot.delete_message(bot_ask_move)
        return move

    async def make_bet(self, ctx):

        def is_float(string):
            try:
                float(string)
                return True
            except ValueError:
                return False

        await self.bot.say("Bet? ")
        await asyncio.sleep(1.0)
        bet = await self.bot.wait_for_message(timeout=20)

        if bet.content.lower().startswith("t."):
            return

        if bet.content.lower() == 'q' or bet.content.lower() == 'quit':
            bet = -1
            return bet

        while True:
            try:

                if ctx.message.author.id != self.player_id:
                    await self.bot.say("Only **{0}** can bet".format(self.player_name))
                    await asyncio.sleep(1.0)
                    bet = await self.bot.wait_for_message(timeout=15)

                elif not is_float(bet.content):
                    await self.bot.say("Invalid bet. Bet? ")
                    await asyncio.sleep(1.0)
                    bet = await self.bot.wait_for_message(timeout=15)

                elif Decimal(bet.content).as_tuple().exponent < -2:
                    await self.bot.say("Invalid bet. Bet? ")
                    await asyncio.sleep(1.0)
                    bet = await self.bot.wait_for_message(timeout=15)

                elif Decimal(bet.content) < 1:
                    await self.bot.say("Bet must be over 1. Bet? ")
                    await asyncio.sleep(1.0)
                    bet = await self.bot.wait_for_message(timeout=15)

                elif Decimal(bet.content) > self.money:
                    await self.bot.say("Bet is too high. Bet? ")
                    await asyncio.sleep(1.0)
                    bet = await self.bot.wait_for_message(timeout=15)

                else:
                    break

            except ValueError:
                await self.bot.say("Invalid bet. Bet? ")
                await asyncio.sleep(1.0)
                bet = await self.bot.wait_for_message(timeout=15)

        self.money -= Decimal(bet.content)
        return Decimal(bet.content)


class Game:

    def __init__(self, server, server_id, player_id, bot=None):

        self.bot = bot
        self.server = server
        self.dealer = Hand()
        self.player = Player(server_id, player_id, server.get_member(player_id).display_name, self.bot)
        self.player_id = player_id
        self.player_name = self.server.get_member(self.player_id).display_name
        self.hands = [Hand()]
        self.deck = Deck()

    def display(self):

        dealer_text = ""
        player_text = ""

        for card in self.dealer.cards:
            dealer_text += str(card)

        if len(self.hands) == 2:
            player_text2 = ""

            for card in self.hands[0].cards:
                player_text += str(card)
            for card in self.hands[1].cards:
                player_text2 += str(card)

            text = ("\nDealer\n {0}" "\n\n{1}\n {2} and {3}"
                    .format(dealer_text, self.player_name, player_text, player_text2))

        else:
            for card in self.hands[0].cards:
                player_text += str(card)

            text = "\nDealer\n {0}" "\n\n{1}\n {2}".format(dealer_text, self.player_name, player_text)

        return '```' + text + '```'

    def money_display(self):

        text = "**{0}**'s money is: ".format(self.server.get_member(self.player_id).display_name) + "${0:,.2f}"\
            .format(self.player.money)

        return text

    async def play(self, ctx):

        dealerstay, playerstay, split, justsplit = False, [], [], False
        doubled = False
        await self.bot.say(self.money_display())

        bet = await self.player.make_bet(ctx)

        if not bet:
            return

        if bet == -1:
            await self.bot.say("**{0}** has quit".format(self.player_name))
            return

        self.hands[0].bet = bet

        curr_game = await self.bot.say(self.display())

        while True:

            curr_game = await self.bot.edit_message(curr_game, self.display())
            #await self.bot.say(self.display())

            if self.dealer.valid_moves == 'blackjack':

                await self.bot.say("Dealer Blackjack")

                for hand in self.hands:
                    if hand.valid_moves == 'blackjack':
                        await self.bot.say("**{0}**'s Blackjack. Push".format(self.player_name))
                        self.player.money += hand.bet
                        continue
                await self.bot.say(self.money_display())
                return

            if dealerstay and len(playerstay) == 2:

                for i in range(len(self.hands)):

                    if max(self.hands[i].scores) == max(self.dealer.scores):
                        await self.bot.say("Push on hand " + str(i+1))
                        self.player.money += self.hands[i].bet

                    elif max(self.hands[i].scores) > max(self.dealer.scores):
                        await self.bot.say(("**{0}** wins on hand " + str(i+1)).format(self.player_name))
                        self.player.money += (2 * self.hands[i].bet)

                    else:
                        await self.bot.say("Dealer wins on hand " + str(i+1))

                await self.bot.say(self.money_display())
                return

            #need to fix this maybe not
            for hand in self.hands:
                if hand.valid_moves == 'blackjack':
                    await self.bot.say("**{0}**'s Blackjack".format(self.player_name))
                    self.player.money += (Decimal(2.5)*hand.bet)
                    self.hands.remove(hand)
                    if not self.hands:
                        await self.bot.say(self.money_display())
                        return
                    continue

                if dealerstay and hand in playerstay:
                    if max(hand.scores) == max(self.dealer.scores):
                        await self.bot.say("Push")
                        self.player.money += hand.bet
                        self.hands.remove(hand)
                        if not self.hands:
                            await self.bot.say(self.money_display())
                            return
                        continue

                    elif max(hand.scores) > max(self.dealer.scores):
                        await self.bot.say("**{0}** wins".format(self.player_name))

                        self.player.money += (2*hand.bet)
                        self.hands.remove(hand)
                        if not self.hands:
                            await self.bot.say(self.money_display())
                            return
                        continue

                    else:
                        await self.bot.say("Dealer wins")
                        self.hands.remove(hand)
                        if not self.hands:
                            await self.bot.say(self.money_display())
                            return
                        continue

                if hand not in playerstay:
                    if doubled and "double" in hand.valid_moves:
                        hand.valid_moves.remove("double")
                    move = await self.player.make_move(ctx, hand)

                    if not move:
                        return

                    if move == -1:
                        await self.bot.say(self.money_display())
                        await self.bot.say("**{0}** has quit".format(self.player_name))
                        return

                    if move == 'double':
                        doubled = True

                #players turn
                while True:

                    if hand in playerstay:
                        break

                    if move == 'quit' or move == 'q':
                        return

                    if move == 'stay':
                        playerstay.append(hand)
                        break

                    if move == 'hit':
                        card = self.deck.deal()
                        hand.add(card)
                        curr_game = await self.bot.edit_message(curr_game, self.display())
                        if hand.valid_moves == 'bust':
                            await self.bot.say("**{0}** busts".format(self.player_name))
                            self.hands.remove(hand)
                            if not self.hands:
                                await self.bot.say(self.money_display())
                                return
                        break

                    if move == 'double':
                        self.player.money -= hand.bet
                        hand.bet *= 2

                        card = self.deck.deal()
                        hand.add(card)
                        curr_game = await self.bot.edit_message(curr_game, self.display())
                        if hand.valid_moves == 'bust':
                            await self.bot.say("**{0}** busts".format(self.player_name))
                            self.hands.remove(hand)
                            if not self.hands:
                                await self.bot.say(self.money_display())
                                return
                        playerstay.append(hand)
                        break

                    if move == 'split':
                        splitcard = hand.cards[-1]
                        split += [Hand(hand.bet), Hand(hand.bet)]
                        self.player.money -= hand.bet
                        #split[0].split_status[0] = split[1].split_status[0] = True
                        split[0].add(splitcard)
                        split[1].add(splitcard)
                        for i in range(len(split)):
                            card = self.deck.deal()
                            split[i].add(card)

                        break

            if split:
                self.hands = split
                split = []
                justsplit = True

            #dealers turn
            while True:

                if dealerstay:
                    break

                if justsplit:
                    justsplit = False
                    break

                scores = self.dealer.scores
                soft = False
                if len(scores) == 2:
                    soft = True

                if (not soft and max(scores) < 17) or (soft and max(scores) <= 17):
                    dealer_msg = await self.bot.say("Dealer hits")
                    card = self.deck.deal()
                    self.dealer.add(card)
                    await asyncio.sleep(2.0)
                    await self.bot.delete_message(dealer_msg)
                    curr_game = await self.bot.edit_message(curr_game, self.display())
                    if self.dealer.valid_moves == 'bust':

                        for hand in self.hands:
                            self.player.money += (2*hand.bet)

                        await self.bot.say("Dealer busts")
                        await self.bot.say(self.money_display())
                        return
                    break

                else:
                    dealerstay = True
                    dealer_msg = await self.bot.say("Dealer stays")
                    await asyncio.sleep(2.0)
                    await self.bot.delete_message(dealer_msg)
                    break

    def deal(self):

        self.deck.populate()
        self.deck.shuffle()
        for _ in range(2):
            card = self.deck.deal()
            self.hands[0].add(card)
            card = self.deck.deal()
            self.dealer.add(card)

