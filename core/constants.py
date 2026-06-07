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
# --- COMPANY DETAILS ---
COMPANY_NAME = "Bold & Italic"
COMPANY_CO = "c/o Stoic Social LLP"
COMPANY_ADDRESS = "Hyderabad, Telangana\nIndia"
COMPANY_GST = "36AFEFS7497C1ZM"
COMPANY_PAN = "AFEFS7497C"
COMPANY_STATE = "Telangana" # Used for strict CGST/SGST vs IGST routing

# --- BANK DETAILS ---
# (Update these with your actual account numbers)
BANK_NAME = "YES BANK"
BANK_ACCOUNT_NAME = "Stoic Social LLP"
BANK_ACCOUNT_NO = "041363400009611" 
BANK_IFSC = "YESB0000413"
