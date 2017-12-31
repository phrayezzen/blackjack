from time import sleep
from Deck import Card, Deck

SHUFFLE_LIMIT = 25
ACTIONS = ['H', 'S', 'D', 's', 'X']  # hit, stand, double, split, surrender
TENS = [10, 11, 12, 13]

class Hand(object):
    def __init__(self, bet):
        self.cards = []
        self.bet = bet
        self.done = False
        self.won = None
        self.soft = False
        self.doubled = False

    @property
    def value(self):
        values = sorted([min(card.value, 10) for card in self.cards], reverse=True)
        total_value = 0
        self.soft = False
        for value in values:
            self.soft = False or self.soft
            total_value += value
            if value == 1 and total_value <= 11:
                total_value += 10
                self.soft = True
        return total_value

    @property
    def is_busted(self):
        return self.value > 21

    @property
    def is_blackjack(self):
        return len(self.cards) == 2 and self.value == 21

    @property
    def is_splittable(self):
        """
        This should be easy to calculate, but we need to check if TJQK are equal value.
        """
        return len(self.cards) == 2 and (self.cards[0].value == self.cards[1].value or (self.cards[0].value in TENS and self.cards[1].value in TENS))

    def hit(self, card):
        """Adds another card to current hand."""
        self.cards.append(card)
        if self.is_busted:
            self.done = True
            self.won = False
            print 'BUSTED!'

    def stand(self):
        """Stops adding cards to hand."""
        self.done = True

    def double_down(self, card):
        """
        Double your bet, add exactly one more card to hand.
        Only allowed on first turn.
        """
        self.bet *= 2
        self.doubled = True
        self.hit(card)
        self.stand()

    def split(self):
        """
        Split your hand into two hands.
        Only allowed on first turn.
        Only allowed if two cards dealt are equal.

        Returns a second hand.
        """
        new_hand = Hand(self.bet)
        new_hand.hit(self.cards[1])
        self.cards = [self.cards[0]]
        return new_hand

    def surrender(self):
        """
        Lose hand and get half your bet back.
        Only allowed on first turn.
        """
        self.done = True
        self.won = False
        self.bet /= 2

    def blackjack(self):
        """
        Payout 2:1 for 21 hand value.
        Automatic.
        Only allowed on first turn.

        Payout happens immediately, not at the end of round, so bet is set to 0.
        This is to handle a niche edge case where both player and dealer
        get blackjack.
        """
        print 'BLACKJACK!'
        sleep(0.5)
        self.done = True
        self.won = True
        self.bet = 0

    def __str__(self):
        modifier = ''
        if self.soft:
            modifier = 'a'
        if self.is_splittable:
            modifier = 's'
        return ' '.join(map(str, self.cards)) + ' (%d%s)' % (self.value, modifier)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        return self.cards[key]

    def __len__(self):
        return len(self.cards)


class Player(object):
    def __init__(self, number=1, money=100):
        self.number = number
        self.money = money
        self.hands = []
        self.hand_index = 0

    @property
    def active_hand(self):
        return self.hands[self.hand_index]

    @property
    def done(self):
        return self.hand_index >= len(self.hands)

    def bet(self, bet=0):
        """Returns if bet was valid."""
        if bet > self.money:
            return False
        self.money -= bet
        self.hands = [Hand(bet)]
        self.hand_index = 0
        return True

    def handle_split(self):
        new_hand = self.active_hand.split()
        self.hands.insert(self.hand_index + 1, new_hand)
        self.money -= new_hand.bet

    def __str__(self):
        return 'Player %d' % self.number


class Blackjack(object):
    def __init__(self, num_decks=2, num_players=1):
        self.num_decks = num_decks
        self.deck = Deck(num_decks)
        self.deck.shuffle()
        self.dealer = Player()  # special player
        self.players = []
        self.round = 0

    def reshuffle(self):
        self.deck = Deck(self.num_decks)
        self.deck.shuffle()

    def start(self):
        print 'Welcome to Blackjack Simulator!'
        num_players = int(raw_input('How many players? ') or 1)
        for i in xrange(num_players):
            money = int(raw_input('How much money does Player %d start with? ' % (i + 1)) or 100)
            self.players.append(Player(i + 1, money=money))

        while True:
            print ''
            self.start_round()

    def start_round(self):
        self.round += 1
        print 'Round %d' % self.round
        if len(self.deck) < SHUFFLE_LIMIT:
            print 'Shuffling deck...'
            self.reshuffle()

        # collect bets
        self.dealer.bet(0)
        for player in self.players:
            print '%s money:' % str(player), player.money
            while True:
                try:
                    bet = int(raw_input('How much does %s bet? ' % str(player)) or 5)
                    print 'Bet:', bet
                    if not player.bet(bet):
                        print 'You do not have that much money!'
                        player.money += int(raw_input('Add some money? ') or 100)
                        continue
                    break
                except ValueError:
                    continue
        print ''

        # deal hands
        for player in self.players:
            if not player.done:
                player.active_hand.hit(self.deck.deal())
        self.dealer.active_hand.hit(self.deck.deal())
        # nuance - deal in rounds, not two at a time
        for player in self.players:
            if not player.done:
                player.active_hand.hit(self.deck.deal())
        self.dealer.active_hand.hit(self.deck.deal())

        # print out hands
        print '========'
        print 'Dealer:'
        print self.dealer.active_hand[0], '??'
        print '========'
        print ''

        for player in self.players:
            if not player.done:
                print '%s:' % str(player)
                print player.active_hand
                print ''
                if player.active_hand.is_blackjack:
                    player.money += 3 * player.active_hand.bet
                    player.active_hand.blackjack()
                    player.hand_index += 1

        # check_dealer_blackjack
        if self.check_dealer_blackjack():
            return

        # player turns
        for player in self.players:
            self.player_turn(player)
            print ''
        self.dealer_turn()
        print ''

        # calculate payout
        self.calculate_payout()

    def check_dealer_blackjack(self):
        hand = self.dealer.active_hand
        if hand[0].value != 1 and hand[0].value not in TENS:
            return

        insurances = [0 for i in xrange(len(self.players))]
        if hand[0].value == 1:
            print 'Dealer has an Ace. Insurance?'
            for player in self.players:
                if not player.done:
                    insurance = max(player.money, player.active_hand.bet) + 1
                    while insurance > player.active_hand.bet / 2 or insurance > player.money:
                        insurance = int(raw_input('%s: ' % player) or 0)
                    insurances[player.number - 1] = insurance
                    player.money -= insurance
            print ''

        if hand.is_blackjack:
            print hand
            print 'DEALER BLACKJACK!'
            sleep(0.5)
            for player in self.players:
                insurance = insurances[player.number - 1]
                player.money += 3 * insurance
                if not player.done:
                    player.active_hand.won = False
                player.hand_index += 1

    def player_turn(self, player):
        print "%s's turn" % player

        while not player.done:
            first_turn = True
            while not player.active_hand.done:
                while len(player.active_hand) < 2:
                    player.active_hand.hit(self.deck.deal())
                print player.active_hand

                if first_turn and player.active_hand.value == 21:
                    player.money += 3 * player.active_hand.bet
                    player.active_hand.blackjack()
                    continue

                action = ''
                while action not in ACTIONS:
                    action = raw_input('Action? ')

                if action == 'H':
                    player.active_hand.hit(self.deck.deal())
                elif action == 'S':
                    player.active_hand.stand()
                elif action == 'D':
                    if not first_turn or player.money < player.active_hand.bet:
                        print 'Not allowed!'
                        continue
                    player.money -= player.active_hand.bet
                    player.active_hand.double_down(self.deck.deal())
                elif action == 's' and first_turn:
                    if not first_turn or not player.active_hand.is_splittable or player.money < player.active_hand.bet:
                        print 'Not allowed!'
                        continue
                    player.handle_split()
                elif action == 'X' and first_turn:
                    if not first_turn:
                        print 'Not allowed!'
                        continue
                    player.active_hand.surrender()
                    player.money += player.active_hand.bet

                first_turn = False or action == 's'

            print player.active_hand
            sleep(0.2)
            player.hand_index += 1

    def dealer_turn(self):
        print "Dealer's turn"
        hand = self.dealer.active_hand
        print hand

        # do not deal more if game is over
        needs_dealing = False
        for player in self.players:
            for phand in player.hands:
                if phand.won is None:
                    needs_dealing = True
                    break
            if needs_dealing:
                break
        if not needs_dealing:
            print 'Everyone has blackjack or lost'
            return
        
        while hand.value < 17 or (hand.value == 17 and hand.soft):
            sleep(0.5)
            hand.hit(self.deck.deal())
            print hand
        sleep(0.5)

    def calculate_payout(self):
        for player in self.players:
            print player
            for hand in player.hands:
                if hand.won is None:
                    hand.won = self.dealer.active_hand.is_busted or hand.value > self.dealer.active_hand.value
                    if hand.value == self.dealer.active_hand.value and not hand.is_busted:
                        hand.won = None  # weird PUSH state

                if hand.is_blackjack:
                    message = 'BLACKJACK!!'
                elif hand.won is True:
                    message = 'WON!'
                    player.money += 2 * hand.bet
                    if hand.doubled:
                        message += ' x2'
                elif hand.won is False:
                    message = 'Lost...'
                elif hand.won is None:
                    message = 'Push'
                    player.money += hand.bet
                print hand, message
            print 'Money: %d' % player.money


if __name__ == '__main__':
    game = Blackjack(num_decks=1)
    game.start()
