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

    @property
    def value(self):
        values = sorted([min(card.value, 10) for card in self.cards], reverse=True)
        total_value = 0
        for value in values:
            self.soft = False
            total_value += value
            if value == 1 and total_value <= 11:
                total_value += 10
                self.soft = True
        return total_value

    @property
    def busted(self):
        return self.value > 21

    @property
    def splittable(self):
        """
        This should be easy to calculate, but we need to check if TJQK are equal value.
        """
        return self.cards[0].value == self.cards[1].value or (self.cards[0].value in TENS and self.cards[1].value in TENS)

    def hit(self, card):
        """Adds another card to current hand."""
        self.cards.append(card)
        if self.busted:
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

    def __str__(self):
        return ' '.join(map(str, self.cards)) + ' (%d)' % self.value

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
        self.hands = [Hand(bet)]
        self.hand_index = 0
        return True

    def handle_split(self):
        new_hand = self.active_hand.split()
        self.hands.insert(self.hand_index, new_hand)

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
        print 'Welcome to Blackjack Simulator'
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
            bet = int(raw_input('How much does %s bet? ' % str(player)) or 5)
            print 'Bet:', bet
            if not player.bet(bet):
                print 'You do not have that much money!'
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
        print 'Dealer:'
        print self.dealer.active_hand[0], '??'
        print ''

        for player in self.players:
            if not player.done:
                print '%s:' % str(player)
                print player.active_hand
                print ''

        # handle dealer ACE - ask for insurance
        if self.check_dealer_blackjack():
            continue

        # player turns
        for player in self.players:
            self.player_turn(player)
            print ''
        self.dealer_turn()
        print ''

        # calculate payout
        self.calculate_payout()

    def check_dealer_blackjack(self):
        if self.dealer.active_hand[0].value != 1:
            return False

        print 'Dealer has an Ace. Insurance?'
        insurances = [0 for i in xrange(len(self.players))]
        for player in self.players:
            insurances[player.number - 1] = int(raw_input(str(player)) or 0)

        if self.dealer.active_hand[1].value in TENS:
            print self.dealer.active_hand
            print 'DEALER BLACKJACK!'
            for player in self.players:
                insurance = insurances[player.number - 1]
                player.money += 2 * insurance
                print '%s money: %d' % player, player.money
            return True

    def player_turn(self, player):
        print "%s's turn" % player

        while not player.done:
            first_turn = True
            while not player.active_hand.done:
                while len(player.active_hand) < 2:
                    player.active_hand.hit(self.deck.deal())
                print player.active_hand

                if first_turn and player.active_hand.value == 21:
                    print '%s BLACKJACK' % str(player).upper()
                    player.hand_index += 1
                    continue

                action = ''
                while action not in ACTIONS:
                    action = raw_input('Action? ')

                if action == 'H':
                    player.active_hand.hit(self.deck.deal())
                elif action == 'S':
                    player.active_hand.stand()
                elif action == 'D':
                    if not first_turn:
                        print 'Not allowed!'
                        continue
                    player.active_hand.double_down(self.deck.deal())
                elif action == 's' and first_turn:
                    if not first_turn or not player.active_hand.splittable:
                        print 'Not allowed!'
                        continue
                    player.handle_split()
                elif action == 'X' and first_turn:
                    if not first_turn:
                        print 'Not allowed!'
                        continue
                    player.active_hand.surrender()

                first_turn = False or action == 's'

            print player.active_hand
            player.hand_index += 1

    def dealer_turn(self):
        from time import sleep
        print "Dealer's turn"
        hand = self.dealer.active_hand
        print hand

        # do not deal more if game is over
        all_lost = True
        for player in self.players:
            for phand in player.hands:
                if phand.won is None:
                    all_lost = False
                    break
            if not all_lost:
                break
        if all_lost:
            print 'Everyone lost...'
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
                    hand.won = self.dealer.active_hand.busted or hand.value > self.dealer.active_hand.value
                    if hand.value == self.dealer.active_hand.value and not hand.busted:
                        hand.won = None  # weird PUSH state

                if hand.won is True:
                    message = 'WON!'
                    player.money += hand.bet                    
                elif hand.won is False:
                    message = 'Lost...'
                    player.money -= hand.bet
                elif hand.won is None:
                    message = 'Push'
                print hand, message
            print 'Money: %d' % player.money


if __name__ == '__main__':
    game = Blackjack(num_decks=1)
    game.start()
