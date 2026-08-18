***Payment system ***
so there will be deadline & milestone(AI work log) client frelancer will fix the milestone kotodin chara chara milestone porbe ! and the payment will be equally distribute to the milestone wise 

suppose client decide the milestone/ month then also the money will be distribute equally 



***Issue's ***
1. No suggestions found from client Dashboard.
2. Integrate Email system for both side 
3. frelanccer can't ad specific skill -- fixed
4. ad rate limiting for for charges and bio sentence -- done 
5. Basic validation for portfolio or github link -- done 
6. Stuck in frelancer profile image uploading section -- 
7. When user sign it with out create accout he redirect as frelancer 
8.  if a user go back with out giving her email it stuck in redirecting in the login page

11. Read Receipt : Verify if messages are marked as read.

14. in the payment page we have to saw the commition we deduct 





### Freelancer Side
- [ ] **Daily Worklog**: Submit a standard daily worklog (Date, Hours Worked, Description, Screenshot proof).
- [ ] **AI Deliverable Submission**: Start the AI workflow to submit a deliverable.
- [ ] **AI Chat Interaction**: Chat with the AI Assistant to describe the work done.
- [ ] **AI Summary Generation**: Ensure the AI successfully generates a structured report/transcript of the work.
- [ ] **Submit for Review**: Submit the final deliverable to the client.

### Client Side
- [ ] **Review Worklog/Deliverable**: View the submitted deliverable and the AI-generated summary.
- [ ] **Approve/Reject**: Approve the deliverable or request revisions (leave client notes/feedback).


 ### System / Background Tasks
- [ ] **Weekly Reports**: Verify that weekly AI-generated progress reports (PDFs) are generated for the contract and stored via Azure Blob Storage URLs.
- [ ] **Delivery Proof**: Upon project completion, verify the final tamper-evident PDF is generated.



## 5. Worklogs, Deliverables, & AI Workflow
Test the core delivery and time-tracking features.



### System / Background Tasks
- [ ] **Weekly Reports**: Verify that weekly AI-generated progress reports (PDFs) are generated for the contract and stored via Azure Blob Storage URLs.
- [ ] **Delivery Proof**: Upon project completion, verify the final tamper-evident PDF is generated.


**Client Recommendation Dashboard**: Verify that relevant freelancers are recommended to the client based on the project's required skills.




***Notification system ***
💼 Client Notifications- 
BID_SUBMITTED	A freelancer applies to one of the client's open projects.	Alerts the client to review the proposal and bid details.

LOG_SUBMITTED	The freelancer logs/submits a milestone for review.	Prompts the client to approve the work and release the funded milestone escrow.

PROOF_READY	The freelancer uploads final delivery proof/deliverables.	Signals the project is ready for final approval.

MESSAGE_RECEIVED	The freelancer sends a direct chat message to the client.	Live notify the client of incoming messages.


🛠️ Freelancer Notifications-
BID_ACCEPTED	The client accepts the freelancer's bid and creates a contract proposal.	Prompts the freelancer to review and accept the contract proposal to start.

ESCROW_CREATED	The client deposits funds into the milestone's escrow wallet.	Notifies the freelancer that funds are secured and they are safe to begin work.

PAYMENT_RELEASED	The client approves a milestone, releasing escrow funds.	Confirms money has been sent to the freelancer's earnings page.

REPORT_UPCOMING	Scheduled weekly report is 3 days away.	Reminds the freelancer to log all recent hours so they get captured in the PDF report.

REPORT_READY	The weekly report PDF generation is completed.	Notifies the freelancer that their copy of the progress report is ready.

MESSAGE_RECEIVED	The client sends a direct chat message to the freelancer.	Live notify the freelancer of incoming messages.
