EMPLOYEES = ["Abhiram", "Bubby", "STC", "Tarun", "Vicky"]

DEFAULT_MAPPING_RULES = [
    {"keyword": "RAZORPAY.*SHIPROCKET", "entity": "Bold and Italic", "person": "Vendor", "remarks": "Shiprocket recharge", "match": "Ignore"},
    {"keyword": "RAZORPAY", "entity": "Bold and Italic", "person": "Customer", "remarks": "Razorpay deposits", "match": "Ignore"},
    {"keyword": "FACEBOOK|PAYUPAYMENT", "entity": "Bold and Italic", "person": "Vendor", "remarks": "Digital Ads / Gateway", "match": "Ignore"},
    {"keyword": "TRIPURA BIO|VUESOL|DR RAJU|CHANDANA SKIN|MAANGALYA|MICKS PROD|INREMIT", "entity": "Socialight", "person": "Client", "remarks": "Client payment", "match": "Yes"},
    {"keyword": "TARUN KUMAR", "entity": "Socialight", "person": "Tarun", "remarks": "SS Salary / Reimbursement", "match": "Yes"},
    {"keyword": "MOHD SHA MAHABOOB|VICKY", "entity": "Socialight", "person": "Vicky", "remarks": "SS Salary / Reimbursement", "match": "Yes"},
    {"keyword": "THRINAT|RAVULA", "entity": "Socialight", "person": "Thrinath", "remarks": "SS Salary", "match": "Yes"},
    {"keyword": "KONERU|BHAVANA", "entity": "Socialight", "person": "Bubby", "remarks": "SS Salary", "match": "Yes"},
    {"keyword": "ABHIRAM", "entity": "Bold and Italic", "person": "Abhiram", "remarks": "Reimbursement", "match": "Yes"},
    {"keyword": "ENVATO", "entity": "Socialight", "person": "Vendor", "remarks": "Tool Subscription", "match": "Yes"}
]
