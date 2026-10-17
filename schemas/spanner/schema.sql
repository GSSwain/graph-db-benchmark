-- LDBC FinBench Specification - GCP Spanner Relational Table Schema
CREATE TABLE Person (
  id INT64 NOT NULL,
  name STRING(256),
  isBlocked BOOL,
  createTime INT64,
  gender STRING(32),
  birthday INT64,
  country STRING(64),
  city STRING(64)
) PRIMARY KEY (id);

CREATE TABLE Company (
  id INT64 NOT NULL,
  name STRING(256),
  isBlocked BOOL,
  createTime INT64,
  country STRING(64),
  city STRING(64),
  business STRING(128),
  description STRING(1024)
) PRIMARY KEY (id);

CREATE TABLE Account (
  id INT64 NOT NULL,
  createTime INT64,
  isBlocked BOOL,
  type STRING(32),
  nickname STRING(64),
  phonenum STRING(32),
  freqLoginType STRING(32),
  lastLoginTime INT64,
  accountLevel STRING(32)
) PRIMARY KEY (id);

CREATE TABLE Loan (
  id INT64 NOT NULL,
  loanAmount INT64,
  balance INT64,
  createTime INT64,
  usage STRING(128),
  interestRate FLOAT64
) PRIMARY KEY (id);

CREATE TABLE Medium (
  id INT64 NOT NULL,
  medType STRING(32),
  isBlocked BOOL,
  createTime INT64,
  lastLogin INT64
) PRIMARY KEY (id);

CREATE TABLE Transfer (
  fromId INT64 NOT NULL,
  toId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  amount INT64,
  orderNum INT64
) PRIMARY KEY (fromId, toId, createTime);

CREATE TABLE Withdraw (
  fromId INT64 NOT NULL,
  toId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  amount INT64
) PRIMARY KEY (fromId, toId, createTime);

CREATE TABLE Repay (
  accountId INT64 NOT NULL,
  loanId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  amount INT64
) PRIMARY KEY (accountId, loanId, createTime);

CREATE TABLE Deposit (
  loanId INT64 NOT NULL,
  accountId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  amount INT64
) PRIMARY KEY (loanId, accountId, createTime);

CREATE TABLE SignIn (
  mediumId INT64 NOT NULL,
  accountId INT64 NOT NULL,
  createTime INT64 NOT NULL
) PRIMARY KEY (mediumId, accountId, createTime);

CREATE TABLE PersonOwnAccount (
  personId INT64 NOT NULL,
  accountId INT64 NOT NULL,
  createTime INT64 NOT NULL
) PRIMARY KEY (personId, accountId);

CREATE TABLE CompanyOwnAccount (
  companyId INT64 NOT NULL,
  accountId INT64 NOT NULL,
  createTime INT64 NOT NULL
) PRIMARY KEY (companyId, accountId);

CREATE TABLE PersonApplyLoan (
  personId INT64 NOT NULL,
  loanId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  organization STRING(128)
) PRIMARY KEY (personId, loanId);

CREATE TABLE CompanyApplyLoan (
  companyId INT64 NOT NULL,
  loanId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  organization STRING(128)
) PRIMARY KEY (companyId, loanId);

CREATE TABLE PersonGuaranteePerson (
  fromPersonId INT64 NOT NULL,
  toPersonId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  relation STRING(64)
) PRIMARY KEY (fromPersonId, toPersonId, createTime);

CREATE TABLE CompanyGuaranteeCompany (
  fromCompanyId INT64 NOT NULL,
  toCompanyId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  relation STRING(64)
) PRIMARY KEY (fromCompanyId, toCompanyId, createTime);

CREATE TABLE Invest (
  investorId INT64 NOT NULL,
  companyId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  ratio FLOAT64
) PRIMARY KEY (investorId, companyId, createTime);

CREATE TABLE WorkIn (
  personId INT64 NOT NULL,
  companyId INT64 NOT NULL,
  createTime INT64 NOT NULL,
  comment STRING(256)
) PRIMARY KEY (personId, companyId);
