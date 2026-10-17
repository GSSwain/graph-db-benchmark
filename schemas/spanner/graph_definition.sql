-- LDBC FinBench Specification - GCP Spanner Graph Property Graph Definition
CREATE PROPERTY GRAPH FinBenchGraph
  NODE TABLES (
    Person,
    Company,
    Account,
    Loan,
    Medium
  )
  EDGE TABLES (
    Transfer
      SOURCE KEY (fromId) REFERENCES Account (id)
      DESTINATION KEY (toId) REFERENCES Account (id)
      LABEL transfer,
    Withdraw
      SOURCE KEY (fromId) REFERENCES Account (id)
      DESTINATION KEY (toId) REFERENCES Account (id)
      LABEL withdraw,
    Repay
      SOURCE KEY (accountId) REFERENCES Account (id)
      DESTINATION KEY (loanId) REFERENCES Loan (id)
      LABEL repay,
    Deposit
      SOURCE KEY (loanId) REFERENCES Loan (id)
      DESTINATION KEY (accountId) REFERENCES Account (id)
      LABEL deposit,
    SignIn
      SOURCE KEY (mediumId) REFERENCES Medium (id)
      DESTINATION KEY (accountId) REFERENCES Account (id)
      LABEL signIn,
    PersonOwnAccount
      SOURCE KEY (personId) REFERENCES Person (id)
      DESTINATION KEY (accountId) REFERENCES Account (id)
      LABEL own,
    CompanyOwnAccount
      SOURCE KEY (companyId) REFERENCES Company (id)
      DESTINATION KEY (accountId) REFERENCES Account (id)
      LABEL own,
    PersonApplyLoan
      SOURCE KEY (personId) REFERENCES Person (id)
      DESTINATION KEY (loanId) REFERENCES Loan (id)
      LABEL apply,
    CompanyApplyLoan
      SOURCE KEY (companyId) REFERENCES Company (id)
      DESTINATION KEY (loanId) REFERENCES Loan (id)
      LABEL apply,
    PersonGuaranteePerson
      SOURCE KEY (fromPersonId) REFERENCES Person (id)
      DESTINATION KEY (toPersonId) REFERENCES Person (id)
      LABEL guarantee,
    CompanyGuaranteeCompany
      SOURCE KEY (fromCompanyId) REFERENCES Company (id)
      DESTINATION KEY (toCompanyId) REFERENCES Company (id)
      LABEL guarantee,
    Invest
      SOURCE KEY (investorId) REFERENCES Person (id)
      DESTINATION KEY (companyId) REFERENCES Company (id)
      LABEL invest,
    WorkIn
      SOURCE KEY (personId) REFERENCES Person (id)
      DESTINATION KEY (companyId) REFERENCES Company (id)
      LABEL workIn
  );
