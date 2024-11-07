import xml.etree.ElementTree as ET
import json

JSON_CODES = {
  "200": {
    "name": "Sales",
    "category": "Revenue",
    "description": "Income from any normal business activity"
  },
  "260": {
    "name": "Other Revenue",
    "category": "Revenue",
    "description": "Any other income that does not relate to normal business activity and is not recurring"
  },
  "270": {
    "name": "Interest Income",
    "category": "Revenue",
    "description": "Gross interest income"
  },
  "310": {
    "name": "Cost of Goods Sold",
    "category": "Direct Costs",
    "description": "Cost of goods sold by the business"
  },
  "320": {
    "name": "Direct Wages",
    "category": "Direct Costs",
    "description": "Payment of wages/salary to an employee whose work can be directly linked to the product or service"
  },
  "325": {
    "name": "Direct Expenses",
    "category": "Direct Costs",
    "description": "Expenses incurred that relate directly to earning revenue"
  },
  "400": {
    "name": "Advertising & Marketing",
    "category": "Overhead",
    "description": "Expenses incurred for advertising and marketing"
  },
  "401": {
    "name": "Audit & Accountancy fees",
    "category": "Overhead",
    "description": "Expenses incurred relating to accounting and audit fees"
  },
  "404": {
    "name": "Bank Fees",
    "category": "Overhead",
    "description": "Fees charged by your bank for transactions regarding your bank account(s)"
  },
  "408": {
    "name": "Cleaning",
    "category": "Overhead",
    "description": "Expenses incurred for cleaning business property"
  },
  "412": {
    "name": "Consulting",
    "category": "Overhead",
    "description": "Payments made to consultants"
  },
  "416": {
    "name": "Depreciation Expense",
    "category": "Overhead",
    "description": "The amount of the asset's cost (based on the useful life) that was consumed during the period"
  },
  "418": {
    "name": "Charitable and Political Donations",
    "category": "Overhead",
    "description": "Payments made to charities or political organisations or events"
  },
  "420": {
    "name": "Entertainment-100% business",
    "category": "Overhead",
    "description": "Expenses incurred on entertainment by the business that for income tax purposes are fully deductable"
  },
  "424": {
    "name": "Entertainment - 0%",
    "category": "Overhead",
    "description": "Expenses incurred on entertainment by the business that for income tax purposes are not fully deductable"
  },
  "425": {
    "name": "Postage, Freight & Courier",
    "category": "Overhead",
    "description": "Expenses incurred by the entity on postage, freight & courier costs"
  },
  "429": {
    "name": "General Expenses",
    "category": "Overhead",
    "description": "Expenses incurred that relate to the general running of the business"
  },
  "433": {
    "name": "Insurance",
    "category": "Overhead",
    "description": "Expenses incurred for insuring the business' assets"
  },
  "437": {
    "name": "Interest Paid",
    "category": "Overhead",
    "description": "Interest paid on a business bank account or credit card account"
  },
  "441": {
    "name": "Legal Expenses",
    "category": "Overhead",
    "description": "Expenses incurred on any legal matters"
  },
  "445": {
    "name": "Light, Power, Heating",
    "category": "Overhead",
    "description": "Expenses incurred for lighting, power or heating the business premises"
  },
  "449": {
    "name": "Motor Vehicle Expenses",
    "category": "Overhead",
    "description": "Expenses incurred on the running of business motor vehicles"
  },
  "457": {
    "name": "Operating Lease Payments",
    "category": "Overhead",
    "description": "Expenses incurred on operating expenses such as office rental and vehicle leases (excludes hire purchase agreements)"
  },
  "461": {
    "name": "Printing & Stationery",
    "category": "Overhead",
    "description": "Expenses incurred on printing and stationery"
  },
  "463": {
    "name": "IT Software and Consumables",
    "category": "Overhead",
    "description": "Expenses incurred on software or computer consumables"
  },
  "465": {
    "name": "Rates",
    "category": "Overhead",
    "description": "Payments made to local council for rates"
  },
  "469": {
    "name": "Rent",
    "category": "Overhead",
    "description": "Payments made to lease a building or area"
  },
  "473": {
    "name": "Repairs & Maintenance",
    "category": "Overhead",
    "description": "Expenses incurred on a damaged or run down asset that will bring the asset back to its original condition"
  },
  "477": {
    "name": "Salaries",
    "category": "Overhead",
    "description": "Payment to employees in exchange for their resources"
  },
  "478": {
    "name": "Directors' Remuneration",
    "category": "Overhead",
    "description": "Payments to company directors in exchange for their resources"
  },
  "479": {
    "name": "Employers National Insurance",
    "category": "Overhead",
    "description": "Payment made for National Insurance contributions - business contribution only"
  },
  "480": {
    "name": "Staff Training",
    "category": "Overhead",
    "description": "Expenses incurred in relation to training staff"
  },
  "482": {
    "name": "Pensions Costs",
    "category": "Overhead",
    "description": "Payments made to pension schemes"
  },
  "483": {
    "name": "Medical Insurance",
    "category": "Overhead",
    "description": "Payments made to medical insurance schemes"
  },
  "485": {
    "name": "Subscriptions",
    "category": "Overhead",
    "description": "Expenses incurred by the business in relation to subscriptions, such as magazines and professional bodies"
  },
  "489": {
    "name": "Telephone & Internet",
    "category": "Overhead",
    "description": "Expenses incurred from any business-related phone calls, phone lines, or internet connections"
  },
  "493": {
    "name": "Travel - National",
    "category": "Overhead",
    "description": "Expenses incurred from any domestic business travel"
  },
  "494": {
    "name": "Travel - International",
    "category": "Overhead",
    "description": "Expenses incurred from any international business travel"
  },
  "497": {
    "name": "Bank Revaluations",
    "category": "Expense",
    "description": "Bank account revaluations due for foreign exchange rate changes"
  },
  "498": {
    "name": "Unrealised Currency Gains",
    "category": "Expense",
    "description": "Unrealised currency gains on outstanding items"
  },
  "499": {
    "name": "Realised Currency Gains",
    "category": "Expense",
    "description": "Gains or losses made due to currency exchange rate changes"
  },
  "500": {
    "name": "Corporation Tax",
    "category": "Overhead",
    "description": "Tax payable on business profits"
  },
  "610": {
    "name": "Accounts Receivable",
    "category": "Current Asset",
    "description": "Invoices the business has issued but has not yet collected payment on"
  },
  "611": {
    "name": "Less Provision for Doubtful Debts",
    "category": "Current Asset",
    "description": "A provision anticipating that a portion of accounts receivable will never be collected"
  },
  "620": {
    "name": "Prepayments",
    "category": "Current Asset",
    "description": "An expenditure that has been paid for in advance"
  },
  "630": {
    "name": "Inventory",
    "category": "Inventory",
    "description": "Value of tracked items for resale."
  },
  "710": {
    "name": "Office Equipment",
    "category": "Fixed Asset",
    "description": "Office equipment that is owned and controlled by the business"
  },
  "711": {
    "name": "Less Accumulated Depreciation on Office Equipment",
    "category": "Fixed Asset",
    "description": "The total amount of office equipment costs that has been consumed by the business (based on the useful life)"
  },
  "720": {
    "name": "Computer Equipment",
    "category": "Fixed Asset",
    "description": "Computer equipment that is owned and controlled by the business"
  },
  "721": {
    "name": "Less Accumulated Depreciation on Computer Equipment",
    "category": "Fixed Asset",
    "description": "The total amount of computer equipment costs that has been consumed by the business (based on the useful life)"
  },
  "740": {
    "name": "Buildings",
    "category": "Fixed Asset",
    "description": "Buildings that are owned and controlled by the business"
  },
  "741": {
    "name": "Less Accumulated Depreciation on Buildings",
    "category": "Fixed Asset",
    "description": "The total amount of buildings costs that have been consumed by the business (based on the useful life)"
  },
  "750": {
    "name": "Leasehold Improvements",
    "category": "Fixed Asset",
    "description": "The value added to the leased premises via improvements"
  },
  "751": {
    "name": "Less Accumulated Depreciation on Leasehold Improvements",
    "category": "Fixed Asset",
    "description": "The total amount of leasehold improvement costs that has been consumed by the business (based on the useful life)"
  },
  "760": {
    "name": "Motor Vehicles",
    "category": "Fixed Asset",
    "description": "Motor vehicles that are owned and controlled by the business"
  },
  "761": {
    "name": "Less Accumulated Depreciation on Motor Vehicles",
    "category": "Fixed Asset",
    "description": "The total amount of motor vehicle costs that has been consumed by the business (based on the useful life)"
  },
  "764": {
    "name": "Plant and Machinery",
    "category": "Fixed Asset",
    "description": "Plant and machinery that are owned and controlled by the business"
  },
  "765": {
    "name": "Less Accumulated Depreciation on Plant and Machinery",
    "category": "Fixed Asset",
    "description": "The total amount of plant and machinery cost that has been consumed by the business (based on the useful life)"
  },
  "770": {
    "name": "Intangibles",
    "category": "Fixed Asset",
    "description": "Assets with no physical presence e.g. goodwill or patents"
  },
  "771": {
    "name": "Less Accumulated Amortisation on Intangibles",
    "category": "Fixed Asset",
    "description": "The total amount of intangibles that have been consumed by the business"
  },
  "800": {
    "name": "Accounts Payable",
    "category": "Current Liability",
    "description": "Invoices the company has received from suppliers but have not made payment on"
  },
  "801": {
    "name": "Unpaid Expense Claims",
    "category": "Current Liability",
    "description": "Expense claims typically made by employees/shareholder employees which the business has not made payment on"
  },
  "805": {
    "name": "Accruals",
    "category": "Current Liability",
    "description": "Any services the business has received but have not yet been invoiced for e.g. Accountancy Fees"
  },
  "810": {
    "name": "Income in Advance",
    "category": "Current Liability",
    "description": "Any income the business has received but have not provided the goods or services for"
  },
  "811": {
    "name": "Credit Card Control Account",
    "category": "Current Liability",
    "description": "The amount owing on the company's credit cards"
  },
  "814": {
    "name": "Wages Payable - Payroll",
    "category": "Current Liability",
    "description": "Where this account is set as the nominated Wages Payable account within Payroll Settings, Xero allocates the net wage amount of each pay run created using Payroll to this account"
  },
  "815": {
    "name": "Employee contribution to benefits",
    "category": "Current Liability",
    "description": "Payroll deductions for employee contributions towards payrolled benefits in kind"
  },
  "820": {
    "name": "VAT",
    "category": "Current Liability",
    "description": "The balance in this account represents VAT owing to or from the HMRC. At the end of the VAT period, it is this account that should be used to code against either the 'refunds from' or 'payments to' the HMRC that will appear on the bank statement. Xero has been designed to use only one VAT account to track VAT on income and expenses, so there is no need to add any new VAT accounts to Xero"
  },
  "825": {
    "name": "PAYE Payable",
    "category": "Current Liability",
    "description": "The Amount of PAYE tax due to be paid to the HMRC"
  },
  "826": {
    "name": "NIC Payable",
    "category": "Current Liability",
    "description": "The amount of a business' portion of National Insurance Contribution that is due to be paid to the HMRC"
  },
  "830": {
    "name": "Provision for Corporation Tax",
    "category": "Current Liability",
    "description": "Corporation tax payable to the HMRC"
  },
  "835": {
    "name": "Directors' Loan Account",
    "category": "Current Liability",
    "description": "Monies owed to or from company directors"
  },
  "840": {
    "name": "Historical Adjustment",
    "category": "Current Liability",
    "description": "For any accounting and starting balance adjustments"
  },
  "850": {
    "name": "Suspense",
    "category": "Current Liability",
    "description": "A clearing account"
  },
  "858": {
    "name": "Pensions Payable",
    "category": "Current Liability",
    "description": "Payroll pension payable account"
  },
  "860": {
    "name": "Rounding",
    "category": "Current Liability",
    "description": "An adjustment entry to allow for rounding"
  },
  "868": {
    "name": "Earnings Orders Payable",
    "category": "Current Liability",
    "description": "Payroll earnings order account"
  },
  "877": {
    "name": "Tracking Transfers",
    "category": "Current Liability",
    "description": "Transfers between tracking categories"
  },
  "900": {
    "name": "Loan",
    "category": "Non-current Liability",
    "description": "Any money that has been borrowed from a creditor"
  },
  "910": {
    "name": "Hire Purchase Loan",
    "category": "Non-current Liability",
    "description": "Any goods bought through hire purchase agreements"
  },
  "920": {
    "name": "Deferred Tax",
    "category": "Non-current Liability",
    "description": "Used if there is a timing difference between taxable profits and accounting profits"
  },
  "947": {
    "name": "Student Loan Deductions Payable",
    "category": "Current Liability",
    "description": "Payroll student loan deductions payable account"
  },
  "950": {
    "name": "Capital - x,xxx Ordinary Shares",
    "category": "Equity",
    "description": "Paid up capital"
  },
  "960": {
    "name": "Retained Earnings",
    "category": "Equity",
    "description": "Do not Use"
  },
  "970": {
    "name": "Owner A Funds Introduced",
    "category": "Equity",
    "description": "Funds contributed by the owner"
  },
  "980": {
    "name": "Owner A Drawings",
    "category": "Equity",
    "description": "Withdrawals by the owners"
  }
}

XML_CODES = r"""<instruction for="<account></account>">
<account-type>
    <account-category>Revenue</account-category>
    <account-code>200</account-code>
    <account-name>Sales</account-name>
    <account-description>Income from any normal business activity</account-description>
</account-type>

<account-type>
    <account-category>Revenue</account-category>
    <account-code>260</account-code>
    <account-name>Other Revenue</account-name>
    <account-description>Any other income that does not relate to normal business activity and is not recurring</account-description>
</account-type>

<account-type>
    <account-category>Revenue</account-category>
    <account-code>270</account-code>
    <account-name>Interest Income</account-name>
    <account-description>Gross interest income</account-description>
</account-type>

<account-type>
    <account-category>Direct Costs</account-category>
    <account-code>310</account-code>
    <account-name>Cost of Goods Sold</account-name>
    <account-description>Cost of goods sold by the business</account-description>
</account-type>

<account-type>
    <account-category>Direct Costs</account-category>
    <account-code>320</account-code>
    <account-name>Direct Wages</account-name>
    <account-description>Payment of wages/salary to an employee whose work can be directly linked to the product or service</account-description>
</account-type>

<account-type>
    <account-category>Direct Costs</account-category>
    <account-code>325</account-code>
    <account-name>Direct Expenses</account-name>
    <account-description>Expenses incurred that relate directly to earning revenue</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>400</account-code>
    <account-name>Advertising &amp; Marketing</account-name>
    <account-description>Expenses incurred for advertising and marketing</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>401</account-code>
    <account-name>Audit &amp; Accountancy fees</account-name>
    <account-description>Expenses incurred relating to accounting and audit fees</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>404</account-code>
    <account-name>Bank Fees</account-name>
    <account-description>Fees charged by your bank for transactions regarding your bank account(s)</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>408</account-code>
    <account-name>Cleaning</account-name>
    <account-description>Expenses incurred for cleaning business property</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>412</account-code>
    <account-name>Consulting</account-name>
    <account-description>Payments made to consultants</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>416</account-code>
    <account-name>Depreciation Expense</account-name>
    <account-description>The amount of the asset's cost (based on the useful life) that was consumed during the period</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>418</account-code>
    <account-name>Charitable and Political Donations</account-name>
    <account-description>Payments made to charities or political organisations or events</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>420</account-code>
    <account-name>Entertainment-100% business</account-name>
    <account-description>Expenses incurred on entertainment by the business that for income tax purposes are fully deductable</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>424</account-code>
    <account-name>Entertainment - 0%</account-name>
    <account-description>Expenses incurred on entertainment by the business that for income tax purposes are not fully deductable</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>425</account-code>
    <account-name>Postage, Freight &amp; Courier</account-name>
    <account-description>Expenses incurred by the entity on postage, freight &amp; courier costs</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>429</account-code>
    <account-name>General Expenses</account-name>
    <account-description>Expenses incurred that relate to the general running of the business</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>433</account-code>
    <account-name>Insurance</account-name>
    <account-description>Expenses incurred for insuring the business' assets</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>437</account-code>
    <account-name>Interest Paid</account-name>
    <account-description>Interest paid on a business bank account or credit card account</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>441</account-code>
    <account-name>Legal Expenses</account-name>
    <account-description>Expenses incurred on any legal matters</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>445</account-code>
    <account-name>Light, Power, Heating</account-name>
    <account-description>Expenses incurred for lighting, power or heating the business premises</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>449</account-code>
    <account-name>Motor Vehicle Expenses</account-name>
    <account-description>Expenses incurred on the running of business motor vehicles</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>457</account-code>
    <account-name>Operating Lease Payments</account-name>
    <account-description>Expenses incurred on operating expenses such as office rental and vehicle leases (excludes hire purchase agreements)</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>461</account-code>
    <account-name>Printing &amp; Stationery</account-name>
    <account-description>Expenses incurred on printing and stationery</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>463</account-code>
    <account-name>IT Software and Consumables</account-name>
    <account-description>Expenses incurred on software or computer consumables</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>465</account-code>
    <account-name>Rates</account-name>
    <account-description>Payments made to local council for rates</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>469</account-code>
    <account-name>Rent</account-name>
    <account-description>Payments made to lease a building or area</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>473</account-code>
    <account-name>Repairs &amp; Maintenance</account-name>
    <account-description>Expenses incurred on a damaged or run down asset that will bring the asset back to its original condition</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>477</account-code>
    <account-name>Salaries</account-name>
    <account-description>Payment to employees in exchange for their resources</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>478</account-code>
    <account-name>Directors' Remuneration</account-name>
    <account-description>Payments to company directors in exchange for their resources</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>479</account-code>
    <account-name>Employers National Insurance</account-name>
    <account-description>Payment made for National Insurance contributions - business contribution only</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>480</account-code>
    <account-name>Staff Training</account-name>
    <account-description>Expenses incurred in relation to training staff</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>482</account-code>
    <account-name>Pensions Costs</account-name>
    <account-description>Payments made to pension schemes</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>483</account-code>
    <account-name>Medical Insurance</account-name>
    <account-description>Payments made to medical insurance schemes</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>485</account-code>
    <account-name>Subscriptions</account-name>
    <account-description>Expenses incurred by the business in relation to subscriptions, such as magazines and professional bodies</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>489</account-code>
    <account-name>Telephone &amp; Internet</account-name>
    <account-description>Expenses incurred from any business-related phone calls, phone lines, or internet connections</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>493</account-code>
    <account-name>Travel - National</account-name>
    <account-description>Expenses incurred from any domestic business travel</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>494</account-code>
    <account-name>Travel - International</account-name>
    <account-description>Expenses incurred from any international business travel</account-description>
</account-type>

<account-type>
    <account-category>Expense</account-category>
    <account-code>497</account-code>
    <account-name>Bank Revaluations</account-name>
    <account-description>Bank account revaluations due for foreign exchange rate changes</account-description>
</account-type>

<account-type>
    <account-category>Expense</account-category>
    <account-code>498</account-code>
    <account-name>Unrealised Currency Gains</account-name>
    <account-description>Unrealised currency gains on outstanding items</account-description>
</account-type>

<account-type>
    <account-category>Expense</account-category>
    <account-code>499</account-code>
    <account-name>Realised Currency Gains</account-name>
    <account-description>Gains or losses made due to currency exchange rate changes</account-description>
</account-type>

<account-type>
    <account-category>Overhead</account-category>
    <account-code>500</account-code>
    <account-name>Corporation Tax</account-name>
    <account-description>Tax payable on business profits</account-description>
</account-type>

<account-type>
    <account-category>Current Asset</account-category>
    <account-code>610</account-code>
    <account-name>Accounts Receivable</account-name>
    <account-description>Invoices the business has issued but has not yet collected payment on</account-description>
</account-type>

<account-type>
    <account-category>Current Asset</account-category>
    <account-code>611</account-code>
    <account-name>Less Provision for Doubtful Debts</account-name>
    <account-description>A provision anticipating that a portion of accounts receivable will never be collected</account-description>
</account-type>

<account-type>
    <account-category>Current Asset</account-category>
    <account-code>620</account-code>
    <account-name>Prepayments</account-name>
    <account-description>An expenditure that has been paid for in advance</account-description>
</account-type>

<account-type>
    <account-category>Inventory</account-category>
    <account-code>630</account-code>
    <account-name>Inventory</account-name>
    <account-description>Value of tracked items for resale.</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>710</account-code>
    <account-name>Office Equipment</account-name>
    <account-description>Office equipment that is owned and controlled by the business</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>711</account-code>
    <account-name>Less Accumulated Depreciation on Office Equipment</account-name>
    <account-description>The total amount of office equipment costs that has been consumed by the business (based on the useful life)</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>720</account-code>
    <account-name>Computer Equipment</account-name>
    <account-description>Computer equipment that is owned and controlled by the business</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>721</account-code>
    <account-name>Less Accumulated Depreciation on Computer Equipment</account-name>
    <account-description>The total amount of computer equipment costs that has been consumed by the business (based on the useful life)</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>740</account-code>
    <account-name>Buildings</account-name>
    <account-description>Buildings that are owned and controlled by the business</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>741</account-code>
    <account-name>Less Accumulated Depreciation on Buildings</account-name>
    <account-description>The total amount of buildings costs that have been consumed by the business (based on the useful life)</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>750</account-code>
    <account-name>Leasehold Improvements</account-name>
    <account-description>The value added to the leased premises via improvements</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>751</account-code>
    <account-name>Less Accumulated Depreciation on Leasehold Improvements</account-name>
    <account-description>The total amount of leasehold improvement costs that has been consumed by the business (based on the useful life)</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>760</account-code>
    <account-name>Motor Vehicles</account-name>
    <account-description>Motor vehicles that are owned and controlled by the business</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>761</account-code>
    <account-name>Less Accumulated Depreciation on Motor Vehicles</account-name>
    <account-description>The total amount of motor vehicle costs that has been consumed by the business (based on the useful life)</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>764</account-code>
    <account-name>Plant and Machinery</account-name>
    <account-description>Plant and machinery that are owned and controlled by the business</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>765</account-code>
    <account-name>Less Accumulated Depreciation on Plant and Machinery</account-name>
    <account-description>The total amount of plant and machinery cost that has been consumed by the business (based on the useful life)</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>770</account-code>
    <account-name>Intangibles</account-name>
    <account-description>Assets with no physical presence e.g. goodwill or patents</account-description>
</account-type>

<account-type>
    <account-category>Fixed Asset</account-category>
    <account-code>771</account-code>
    <account-name>Less Accumulated Amortisation on Intangibles</account-name>
    <account-description>The total amount of intangibles that have been consumed by the business</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>800</account-code>
    <account-name>Accounts Payable</account-name>
    <account-description>Invoices the company has received from suppliers but have not made payment on</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>801</account-code>
    <account-name>Unpaid Expense Claims</account-name>
    <account-description>Expense claims typically made by employees/shareholder employees which the business has not made payment on</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>805</account-code>
    <account-name>Accruals</account-name>
    <account-description>Any services the business has received but have not yet been invoiced for e.g. Accountancy Fees</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>810</account-code>
    <account-name>Income in Advance</account-name>
    <account-description>Any income the business has received but have not provided the goods or services for</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>811</account-code>
    <account-name>Credit Card Control Account</account-name>
    <account-description>The amount owing on the company's credit cards</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>814</account-code>
    <account-name>Wages Payable - Payroll</account-name>
    <account-description>Where this account is set as the nominated Wages Payable account within Payroll Settings, Xero allocates the net wage amount of each pay run created using Payroll to this account</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>815</account-code>
    <account-name>Employee contribution to benefits</account-name>
    <account-description>Payroll deductions for employee contributions towards payrolled benefits in kind</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>820</account-code>
    <account-name>VAT</account-name>
    <account-description>The balance in this account represents VAT owing to or from the HMRC. At the end of the VAT period, it is this account that should be used to code against either the 'refunds from' or 'payments to' the HMRC that will appear on the bank statement. Xero has been designed to use only one VAT account to track VAT on income and expenses, so there is no need to add any new VAT accounts to Xero</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>825</account-code>
    <account-name>PAYE Payable</account-name>
    <account-description>The Amount of PAYE tax due to be paid to the HMRC</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>826</account-code>
    <account-name>NIC Payable</account-name>
    <account-description>The amount of a business' portion of National Insurance Contribution that is due to be paid to the HMRC</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>830</account-code>
    <account-name>Provision for Corporation Tax</account-name>
    <account-description>Corporation tax payable to the HMRC</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>835</account-code>
    <account-name>Directors' Loan Account</account-name>
    <account-description>Monies owed to or from company directors</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>840</account-code>
    <account-name>Historical Adjustment</account-name>
    <account-description>For any accounting and starting balance adjustments</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>850</account-code>
    <account-name>Suspense</account-name>
    <account-description>A clearing account</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>858</account-code>
    <account-name>Pensions Payable</account-name>
    <account-description>Payroll pension payable account</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>860</account-code>
    <account-name>Rounding</account-name>
    <account-description>An adjustment entry to allow for rounding</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>868</account-code>
    <account-name>Earnings Orders Payable</account-name>
    <account-description>Payroll earnings order account</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>877</account-code>
    <account-name>Tracking Transfers</account-name>
    <account-description>Transfers between tracking categories</account-description>
</account-type>

<account-type>
    <account-category>Non-current Liability</account-category>
    <account-code>900</account-code>
    <account-name>Loan</account-name>
    <account-description>Any money that has been borrowed from a creditor</account-description>
</account-type>

<account-type>
    <account-category>Non-current Liability</account-category>
    <account-code>910</account-code>
    <account-name>Hire Purchase Loan</account-name>
    <account-description>Any goods bought through hire purchase agreements</account-description>
</account-type>

<account-type>
    <account-category>Non-current Liability</account-category>
    <account-code>920</account-code>
    <account-name>Deferred Tax</account-name>
    <account-description>Used if there is a timing difference between taxable profits and accounting profits</account-description>
</account-type>

<account-type>
    <account-category>Current Liability</account-category>
    <account-code>947</account-code>
    <account-name>Student Loan Deductions Payable</account-name>
    <account-description>Payroll student loan deductions payable account</account-description>
</account-type>

<account-type>
    <account-category>Equity</account-category>
    <account-code>950</account-code>
    <account-name>Capital - x,xxx Ordinary Shares</account-name>
    <account-description>Paid up capital</account-description>
</account-type>

<account-type>
    <account-category>Equity</account-category>
    <account-code>960</account-code>
    <account-name>Retained Earnings</account-name>
    <account-description>Do not Use</account-description>
</account-type>

<account-type>
    <account-category>Equity</account-category>
    <account-code>970</account-code>
    <account-name>Owner A Funds Introduced</account-name>
    <account-description>Funds contributed by the owner</account-description>
</account-type>

<account-type>
    <account-category>Equity</account-category>
    <account-code>980</account-code>
    <account-name>Owner A Drawings</account-name>
    <account-description>Withdrawals by the owners</account-description>
</account-type>

</instruction>"""