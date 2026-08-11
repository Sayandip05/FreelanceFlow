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
9. after accept the bid the frelancer should get a notification
10. when user get message he should get a notification and the first message he got it look like he send the message the message show on send side.

11. Read Receipt : Verify if messages are marked as read.

12. when frelancer click on worklog  -> open ai assistant it simply logout the frelancer

13. payment system not working while client click on fund escrow it show a pop up but not redirect any page for payment 

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

---

## 6. Payments & Escrow (Razorpay)
Test the financial workflow.

### Client Side
- [ ] **Fund Escrow**: Make a payment through Razorpay for a project milestone or upfront contract amount.
- [ ] **Payment Status**: Verify the payment status turns to ESCROWED.

### Client/Freelancer Side
- [ ] **Release Payment**: Client approves work and releases payment from escrow.
- [ ] **Freelancer Payout**: Verify the payment is marked for payout to the freelancer's RazorpayX Fund Account.
- [ ] **Platform Cut**: Check that the platform fee (earning percentage) is deducted correctly.


**Client Recommendation Dashboard**: Verify that relevant freelancers are recommended to the client based on the project's required skills.
