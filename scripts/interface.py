from brownie import network, config, accounts, MockV3Aggregator, Contract
from web3 import Web3

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev", "rinkeby-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]

DECIMALS = 8
STARTING_PRICE = 200000000000


def get_account():
    if (
            network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
            # or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


def deploy_mocks():
    print(f"The active network is {network.show_active()}")
    print("Deploying Mocks...")
    if len(MockV3Aggregator) <= 0:
        MockV3Aggregator.deploy(DECIMALS, STARTING_PRICE, {"from": get_account()})
    print("Mocks Deployed!")


def deploy_contract(contract_cls, cls_name, local_acc_idx, local_constructor_args):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:  # or network.show_active() in FORKED_LOCAL_ENVIRONMENTS:
        if len(local_constructor_args) > 0:
            instance = contract_cls.deploy(*local_constructor_args, {"from": accounts[local_acc_idx]}, publish_source=False)
        else:
            instance = contract_cls.deploy({"from": accounts[local_acc_idx]}, publish_source=False)
    else:  # either testnet or fork
        instance_add = config["networks"][network.show_active()][f"{cls_name}_address"]
        instance = Contract.from_abi(cls_name, instance_add, contract_cls.abi)

    return instance
