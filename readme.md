
Daniel Carpenter  
Date: 10/21/2021  

---


## Understanding the problem
Create a system to receive partner tuition expense line item data by customer user of the partner service, aggregate expenses by said user monthly for each customer, allow customer to approve or deny, and deliver to each customer on approval.

## Some Assumptions

* There are existing TuitionCo upstream or peer systems which are the source of truth for partner and customer information. This seems to be hinted at by there being a Web Portal team. I assume that partners interact with this portal to upload/send the expense line items.
* This is replacing/upgrading what most likely was a partially manual process. As such there are already defined domain types such as expenses with tuition being a type of expense. I would want to know more about the types and process along any expense caveats or "gotchas". 
* Since we are dealing with records concerning usage/payments/billing we will most likely want to audit as much as possible so if there are discrepancies or customers or partners want greater visibility we have a sufficient audit trail of what happened when. There may also be industry compliance requirements as well. I would leverage PgAudit for this
* Other TuitionCo services run on AWS and we can leverage services like SQS for communication between system
* Members of the Invoice system team have sufficient AWS IAM role/group permissions to create the necessary resources
* Extensive Logging will be used in production and there is a centralized logging system to utilize.



## Proposal for the system
Given the load estimates and feature requirements I would start with leveraging Django, Postgres, and a few AWS services. I think this provides a good balance of simplicity, extensibility, and reliability

### Technologies used
- Django for application framework
- Postgres for data persistence
- AWS S3 for storing partner expense line item files and possibly generated invoices for customers
- SQS for receiving events from portal

**Caveat**:
It's probably not really sufficient for customers to use the Django admin framework for approving invoices and should only be really used by TuitionCo team members for manaing system data. If there is an existing standardized approach to interface with the customer, say for example only through the WebPortal perhaps app.tuitionco.com) we would have to work with that team to expose APIs from the invoice system to their frontend so in the case of say a customer clicking on an email link to approve/deny an invoice that opens a link to the WebPortal which in turn queries our API and renders up a table view of the aggregate invoice which they can review and hopefully approve. I stubbed out a react app in the guild_frontend_app in the case we would need to create our own frontend 
### Basic Flow

1. Receive expense line items by customer user from upstream system ( perhaps the web portal service/system referenced in the requirements document).
2. Determine data/file handler, Parse file to text and model/object representation, and persist in database along with basic contextual data
3. Persist expense file to S3
4. as different customers will have different monthly invoice report dates I would want to setup a task queue and leverage periodic tasks to generate the report for the customer, update a customer_reports table and alter the status to something like 'awaiting_approval'.
5. Customer contact is notified through another following task about the generated report and that it requires their approval. On approval the status of the report is changed and the invoice is exported to a csv file (along with the user data).
   1. Later on, we will need to think about how to store customer configuration for how they want their invoices delivered. I am going to assume we have other services and another team will manage the API setup with the customer having an API token or other mechanism such that we can safely send them the invoices programmatically. 
6. The generated file is sent along to the customer and the customers user and we may want to archive the generated invoice in s3 for easy retrieval later. 
7. Later on, for customers that want a more direct integration to their accounting systems we could do anything from POSTing the file itself to something like a webhook or a standard REST API interface. If we implement a REST API we will then need to setup a system to assign tokens for authorization to use the API. Another possibility we may need to consider is an EDI layer if the customer is using a more "traditional" system. Like other parts of the system this will most likely have a high level interface with various implementations depending on the method of integration and delivery.


### Contracts / Interfaces

Using a mix of interface contracts in both python and protobuf we can perhaps quickly sketch certain parts of the system. 

Also since the partner statement makes it clear that not all partners send the same file format we will have to handle different file formats as well as different ways they may specify data. We would need to normalize this somehow into an internal specification. 


```protobuf

message Expense {
    string unit = 1;
    string currency = 2;
    string amount = 3;
    Customer customer = 4;
    enum ExpenseType {
        TUITION = 0
        MATERIALS = 1
        TUTORING = 2
    }
    ExpenseType expense = 5;
}

message CustomerUser {
    string name = 1;
    Customer customer = 2;
    repeated Courses courses = 3;
}

message Customer {
  string name = 1;
  int32 id = 2;
  optional string email = 3;
  
  enum CustomerType {
    CORPORATION = 0;
    PRIVATE = 1;
    NONPROFIT = 2;
  }

  CustomerType customer_type 4;
}

message Partner {
  string name = 1;
  int32 id = 3;
  optional string primary_contact = 3;

  enum PartnerType {
    UNIVERSITY = 0;
    BUSINESS = 1;
    NONPROFIT = 2;
  }
}

```

---

Python "interface" using abc metaclass approach

```python
class ExpenseTypeInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'process') and 
                callable(subclass.process) or 
                NotImplemented)

    @abc.abstractmethod
    def process(self, expense: dict):
        """process expense"""
        raise NotImplementedError

class TuitionExpenseType(ExpenseTypeInterface):
    def process(self, expense: dict ) -> dict:
        pass   
```

The approach in python using abc is somewhat similar to Java's standard of interfaces while one could also use [Protocol from mypy](https://mypy.readthedocs.io/en/latest/protocols.html#simple-user-defined-protocols) and this would be similar to Go's implementation of interfaces. 


```python

# Python interface for handling the parsing of expense line item documents

class ExpenseDataParserInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load_data_source') and 
                callable(subclass.load_data_source) and 
                hasattr(subclass, 'extract_text') and 
                callable(subclass.extract_text) or 
                NotImplemented)

    @abc.abstractmethod
    def load_data(self, path: str, file_name: str):
        """Load data for extraction"""
        raise NotImplementedError

    @abc.abstractmethod
    def extract_text(self, full_file_path: str):
        """Extract text from the data"""
        raise NotImplementedError

class CsvParser(ExpenseDataParserInterface):
    pass 

class DocxParser(ExpenseDataParserInterface):
    pass 
     
```
There is a great overview of metaclasses for subclass validation (Item 48) from *Effective Python 2nd Edition* by Brett Slatkin


### Persistence

I most likely would start with a simple table design for persistence and would only introduce multitenancy if some kind of data isolation was requested from customers. Below is a very rough sketch of a main expense table and a materialized view we could use to generate an aggregate expense report by user. We could leverage celery to run a periodic job to refresh the materialized view.

Something I would still have to think about is the utility of creating separate tables for customers, customer users, and partners. I like the keeping data local but if the source of truth for these entities resides on another service and I most often only need references to the full entity at report generation time I probably can just store the entity references ids necessary to query the service when needed. This has its own weaknesses but for an initial working service I would go this route. 



```sql
CREATE TABLE partner_expenses (
  id bigserial PRIMARY KEY,
  partner_id text,
  expense_type text,
  expense_amount text,
  customer_user_id bigserial REFERENCES customer_users (user_id) ON UPDATE CASCADE # optional
  customer_id text 
  created_at timestamp,
  updated_at timestamp
);

CREATE INDEX ON partner_expense (customer_user_id, customer_id);

CREATE MATERIALIZED VIEW customer_user_invoice_report AS 
SELECT date_trunc('month', created_at) as month,
       customer_user_id,
       customer_id,
       sum(expense_amount) as monthly_sum
FROM partner_expenses
GROUP BY customer_user_id, customer_id;

```
I would handle aggregation using materialized views which offloads what could be expensive aggregation processing using Djangos queryset aggregation. The downside here is that handling materialized views in Django isn't really easily supported out of the box and would require introducting some extra data handling functionality in the model layer. 

### Integration 

I would want to first understand which systems customers used and then try to figure out which approach aligns with most customers integration needs. In most cases we would want some sort of REST API with various mechanisms supported to interact with and consume it.

Though far from complete I would initially sketch out an integration API using Swagger/OpenAPI spec 

```yaml

paths:
  /customers/
  /partners/
  /reporting/reports
  /reporting/reports/{id}
  /reporting/reports/{id}/download
  /reporting/reports/{id}/upload
  /reporting/schedules
  /reporting/schedules/{id}
  /reporting/schedules/{id}/disable
  /reporting/schedules/{id}/enable
  /reporting/schedules/{id}/trigger

```

### Report Generation

Similar to how there is an interface for ingesting expense line items I would have an export interface for exporting to different formats depending on how the customers wanted it. To start we would support CSV but also could export to PDF or whatever other format was needed.

### Development
I would propose using Docker containers and Docker Compose for development to make the system easier to encapsulate and share with other developers. This will also come in handy for build and deployment. My assumption is that this will require less involvement from the aforementioned Configuration team as they will not have to specifically setup a django server environment on an EC2 instance. 

### Infrastructure / Deployment
I would propose setting up intial infrastructure using a Cloudformation template and for CI/CD leveraging AWS CodePipeline 
- to build on pull request / merge to main
- commit updates build action in pipeline
- build runs, performs some basic tests, and upon passing the docker image is pushed to AWS ECR.
- We could configure ECS to update automatically but we may want to avoid that initially and instead start with some kind of scheduled deploy. This will depend on how many instances we are running and if we want to support rolling updates. 

### System Setup

The production system will most likely live in the save VPC as other services with the related resources all being tagged as belonging to the invoice service


## Closing thoughts
I think the above sketch outlines a suitable and pragmatic system which satisfies the mentioned requirements. If I were operating in a microservices or serverless environment I would encapsulate certain things differently but leverage some of the same services such as Postgres, Queues ( SQS ), and S3. Even with the estimated growth I would still stick with postgres but add some capacity and failover mechanisms. Perhaps at some point if the volume of expenses is high enough or other processing requirements are introduced it would make sense to incorporate Redshift. 

 
Also the code is really really messy and won't work but I was curious to start thinking very loosely how I would start creating this. Most of the interesting code is in 

src/guild_invoice/expenses -> service.py, expense_queue

I didn't have anytime to work out more of the invoice generation itself but hopefully we can have a great conversation about it. 