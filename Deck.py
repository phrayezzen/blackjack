SUITS = ['J', 'D', 'C', 'H', 'S']
VALUES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']

class Card(object):
    def __init__(self, suit=1, value=1, string=None):
        """
        0 = joker (value=0 black -- value=1 red)
        1 = diamonds
        2 = clubs
        3 = hearts
        4 = spades
        1 = ace
        11 = jack, etc
        string transforms 'AH' to Card(1, 1)
        """
        if string:
            self.suit = SUITS.index(string[1])
            self.value = VALUES.index(string[0]) + 1
            return
        self.suit = suit
        self.value = value

    def get_formatted_value(self):
        if self.suit == 'J':
            return 'R' if self.value else 'B'
        return VALUES[self.value - 1]

    def get_formatted_suit(self):
        return SUITS[self.suit]

    def __str__(self):
        return self.get_formatted_value() + self.get_formatted_suit()

    def __repr__(self):
        return self.__str__()


class Deck(object):
    def __init__(self, num_decks=1, jokers=False):
        self.deck = [Card(a + 1, b + 1) for a in xrange(len(SUITS) - 1) for b in xrange(len(VALUES)) for i in xrange(num_decks)]
        if jokers:
            self.deck += Card(0, 0)  # black joker
            self.deck += Card(0, 1)  # red joker

    def shuffle(self):
        from random import shuffle
        shuffle(self.deck)

    def deal(self, num_cards=1):
        """
        Returns a list of dealt cards.
        Removes cards from top (front) of deck.
        """
        dealt_cards = self.deck[:num_cards]
        self.deck = self.deck[num_cards:]
        return dealt_cards

    def peek(self, num_cards=1):
        """
        Reveals top card.
        Does not remove from top (front) of deck.
        """
        return self.deck[:num_cards]

    def __add__(self, other):
        self.deck += other.deck
        return self

    def __str__(self):
        return ', '.join(map(str, self.deck))

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    pass
