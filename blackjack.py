from Deck import Card, Deck

SHUFFLE_LIMIT = 25

class Hand(object):
    def __init__(self, bet):
        self.cards = []
        self.bet = bet

    @property
    def value(self):
        values = [min(card.value, 10) for card in self.cards].sorted(reverse=True)
        total_value = 0
        for value in values:
            total_value += value
            if value == 1 and total_value <= 11:
                total_value += 10
        return total_value

    @property
    def busted(self):
        return self.value > 21

    def hit(self, card):
        """Adds another card to current hand."""
        self.cards.append(card)

    def stand(self):
        """Stops adding cards to hand."""
        pass  # no op

    def double_down(self, card):
        """
        Double your bet, add exactly one more card to hand.
        Only allowed on first turn.
        """
        self.bet *= 2
        self.cards.append(card)

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
        """Lose hand and get half your bet back."""
        pass

    def __str__(self):
        return ' '.join(map(str, self.cards))

    def __repr__(self):
        return self.__str__()



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
        return self.hand_index == len(self.hands)

    def bet(self, bet=0):
        """Returns if bet was valid."""
        if bet > self.money:
            return False
        self.hands = [Hand(bet)]
        return True

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

        # deal hands
        for player in self.players:
            player.hands[0].hit(self.deck.deal()[0])
        self.dealer.hands[0].hit(self.deck.deal()[0])
        # nuance - deal in rounds, not two at a time
        for player in self.players:
            player.hands[0].hit(self.deck.deal()[0])
        self.dealer.hands[0].hit(self.deck.deal()[0])

        # print out hands
        print 'House:'
        print self.dealer.hands[0]
        print ''

        for player in self.players:
            print '%s:' % str(player)
            for hand in player.hands:
                print '%s' % str(hand)


        # handle dealer ACE - ask for insurance
        # handle dealer blackjack

        # player turns


if __name__ == '__main__':
    game = Blackjack(num_decks=1)
    game.start()
