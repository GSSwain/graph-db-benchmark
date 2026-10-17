// LDBC FinBench Specification - Neo4j DDL & Indexes
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT loan_id_unique IF NOT EXISTS FOR (l:Loan) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT medium_id_unique IF NOT EXISTS FOR (m:Medium) REQUIRE m.id IS UNIQUE;

CREATE INDEX account_is_blocked IF NOT EXISTS FOR (a:Account) ON (a.isBlocked);
CREATE INDEX account_create_time IF NOT EXISTS FOR (a:Account) ON (a.createTime);
CREATE INDEX account_type IF NOT EXISTS FOR (a:Account) ON (a.type);
CREATE INDEX account_level IF NOT EXISTS FOR (a:Account) ON (a.accountLevel);

CREATE INDEX person_is_blocked IF NOT EXISTS FOR (p:Person) ON (p.isBlocked);
CREATE INDEX person_create_time IF NOT EXISTS FOR (p:Person) ON (p.createTime);
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX person_country IF NOT EXISTS FOR (p:Person) ON (p.country);

CREATE INDEX company_is_blocked IF NOT EXISTS FOR (c:Company) ON (c.isBlocked);
CREATE INDEX company_create_time IF NOT EXISTS FOR (c:Company) ON (c.createTime);

CREATE INDEX loan_create_time IF NOT EXISTS FOR (l:Loan) ON (l.createTime);
CREATE INDEX loan_balance IF NOT EXISTS FOR (l:Loan) ON (l.balance);

CREATE INDEX medium_is_blocked IF NOT EXISTS FOR (m:Medium) ON (m.isBlocked);
CREATE INDEX medium_type IF NOT EXISTS FOR (m:Medium) ON (m.medType);

CREATE INDEX transfer_create_time IF NOT EXISTS FOR ()-[r:transfer]-() ON (r.createTime);
CREATE INDEX transfer_amount IF NOT EXISTS FOR ()-[r:transfer]-() ON (r.amount);
CREATE INDEX transfer_order IF NOT EXISTS FOR ()-[r:transfer]-() ON (r.order);

CREATE INDEX withdraw_create_time IF NOT EXISTS FOR ()-[r:withdraw]-() ON (r.createTime);
CREATE INDEX withdraw_amount IF NOT EXISTS FOR ()-[r:withdraw]-() ON (r.amount);
CREATE INDEX repay_create_time IF NOT EXISTS FOR ()-[r:repay]-() ON (r.createTime);
CREATE INDEX deposit_create_time IF NOT EXISTS FOR ()-[r:deposit]-() ON (r.createTime);
CREATE INDEX sign_in_create_time IF NOT EXISTS FOR ()-[r:signIn]-() ON (r.createTime);
CREATE INDEX own_create_time IF NOT EXISTS FOR ()-[r:own]-() ON (r.createTime);
CREATE INDEX apply_create_time IF NOT EXISTS FOR ()-[r:apply]-() ON (r.createTime);
CREATE INDEX guarantee_create_time IF NOT EXISTS FOR ()-[r:guarantee]-() ON (r.createTime);
CREATE INDEX invest_create_time IF NOT EXISTS FOR ()-[r:invest]-() ON (r.createTime);
CREATE INDEX work_in_create_time IF NOT EXISTS FOR ()-[r:workIn]-() ON (r.createTime);
