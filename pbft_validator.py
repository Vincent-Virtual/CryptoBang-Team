from pbft_wallet import Wallet  # Assuming you have a Wallet class defined

class Validators:
    def __init__(self, number_of_validators):
        self.list = self.generate_addresses(number_of_validators)

    def generate_addresses(self, number_of_validators):
        return [Wallet("NODE" + str(i)).get_public_key() for i in range(number_of_validators)]

    def is_valid_validator(self, validator):
        return validator in self.list

# Assuming you have a Wallet class defined
