"""
LDBC FinBench Data Models
Reference: https://ldbcouncil.org/ldbc_finbench_docs/ldbc-finbench-specification.pdf
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Person:
    id: int
    name: str
    isBlocked: bool
    createTime: int
    gender: str
    birthday: int
    country: str
    city: str

@dataclass
class Company:
    id: int
    name: str
    isBlocked: bool
    createTime: int
    country: str
    city: str
    business: str
    description: str

@dataclass
class Account:
    id: int
    createTime: int
    isBlocked: bool
    type: str              # e.g., "debit", "credit"
    nickname: str
    phonenum: str
    freqLoginType: str     # e.g., "mobile", "web"
    lastLoginTime: int
    accountLevel: str      # e.g., "regular", "silver", "gold", "platinum"

@dataclass
class Loan:
    id: int
    loanAmount: int
    balance: int
    createTime: int
    usage: str
    interestRate: float

@dataclass
class Medium:
    id: int
    medType: str           # e.g., "smartphone", "browser", "pos_terminal"
    isBlocked: bool
    createTime: int
    lastLogin: int

@dataclass
class Transfer:
    fromId: int
    toId: int
    createTime: int
    amount: int
    order: int

@dataclass
class Withdraw:
    fromId: int
    toId: int
    createTime: int
    amount: int

@dataclass
class Repay:
    accountId: int
    loanId: int
    createTime: int
    amount: int

@dataclass
class Deposit:
    loanId: int
    accountId: int
    createTime: int
    amount: int

@dataclass
class SignIn:
    mediumId: int
    accountId: int
    createTime: int

@dataclass
class Own:
    ownerId: int
    ownerType: str        # "Person" or "Company"
    accountId: int
    createTime: int

@dataclass
class Apply:
    applicantId: int
    applicantType: str    # "Person" or "Company"
    loanId: int
    createTime: int
    organization: str

@dataclass
class Guarantee:
    fromId: int
    toId: int
    entityType: str       # "Person" or "Company"
    createTime: int
    relation: str

@dataclass
class Invest:
    investorId: int
    investorType: str     # "Person" or "Company"
    companyId: int
    createTime: int
    ratio: float

@dataclass
class WorkIn:
    personId: int
    companyId: int
    createTime: int
    comment: str
