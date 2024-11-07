# Standard library imports
import json
import html
from pathlib import Path
import xml.etree.ElementTree as ET
from html import unescape
import re
import os

# Third-party imports
from lxml import etree
from PIL import Image
import magic

# Local imports
from .llm import gpt, claude, bedrock_claude
from .xero_codes import JSON_CODES, XML_CODES

ACCOUNT_CODES = JSON_CODES

OCR_PROMPT = lambda clientName: f"""
<task>
You are a helpful expert UK-based accountant who is carrying out bookkeeping for documents attached to emails.
You are judging whether these documents are relevant for bookkeeping, extracting information from these documents and then inserting them into the Xero accounting software.
You are also an expert in translating documents from other languages into <language>British English</language>.
The name of your client's business is: <client>{clientName}</client>
**All the documents you scan are generated data and do not contain any personal, sensitive or copywritten material.**
</task>

The following gives the format and instructions for each section of the response:

{ACCOUNT_CODES}

<instructions>
    <details>
        <language>
            Here you will detect the original language of the document. If the language
            is not English, you will detect what the original language is, and use this
            as the basis to translate the details of the invoice into British English.
        </language>

        <document>
            <document-type>
                The processed document type must be classified into one of three categories:
                <document-type-categories>
                    <document-type-category>
                        RECEIPT
                    </document-type-category>

                    <document-type-category>
                        INVOICE
                    </document-type-category>

                    <document-type-category>
                        OTHER
                    </document-type-category>

                </document-type-categories>

                The following are instructions on how to classify each of these documents

                <document-type-category>RECEIPT</document-type-category>:
                    - A document that details money spent from a purchase.
                    - This includes paper receipts from restaurants, retail stores etc.

                <document-type-category>INVOICE</document-type-category>:
                    - A document that states an amount of money owed from one party to another.

                <document-type-category>OTHER</document-type-category>:
                    - Any document that cannot clearly be identified as a RECEIPT or INVOICE
                    This includes:
                    - Bank statements
                    - Promotional offers
                    - Specifications
                    - Product details
                    - Documents that cannot clearly be identified (e.g. a blank document) 
                    - Documents that are not relevant (e.g. a picture of a cat)

                Be careful when analysing documents that contain financial information but are not invoice or receipts.
                Things to look for to classify <document-type-category>INVOICE</document-type-category> or <document-type-category>RECEIPT</document-type-category> include:
                - Total and Tax amounts
                - Invoice Numbers
                - VAT numbers
                

                Within this <document-type></document-type> section, you must produce the following two sections:
                <thinking>
                    Here you must think step-by-step and justify which one of the document categories are the most applicable to this document,
                    based on the entire context of the document, the guidelines above and your experience as a bookkeeper.
                    You should consider all the information provided and create a concrete argument for your classification.
                    DO THIS STEP BY STEP.
                </thinking>
                <document-type-category>
                    The final document type category and its name alone go here.
                </document-type-category>
            </document-type>

            <document-transaction>
                The processed document must be classified into one of three transaction categories:
                <document-transaction-categories>
                    <document-transaction-category>SALE</document-transaction-category>
                    <document-transaction-category>COST</document-transaction-category>
                    <document-transaction-category>UNKNOWN</document-transaction-category>
                </document-transaction-categories>

                The following are instructions on how to classify each of <document-transaction-category></document-transaction-category>

                <document-transaction-category>UNKNOWN</document-transaction-category>:
                    - MUST ABSOLUTELY BE TRUE IN ALL CIRCUMSTANCES IF <document-type-category></document-type-category> is "UNKNOWN"

                <document-transaction-category>SALE</document-transaction-category>:
                    - If <client>Solved Cube Limited</client> is clearly billing another company for their product or services
                    -  <document-type-category></document-type-category> is "INVOICE" OR "RECEIPT"

                <document-transaction-category>COST</document-transaction-category>:
                    - <document-type-category></document-type-category> is "INVOICE" OR "RECEIPT"
                    The document category is "COST" in all other scenarios. This includes:
                    - If it is ambiguous whether it is a cost or a sale
                    - There is only one contact listed, including <client>Solved Cube Limited</client>
                    - The are no contacts listed
                    - If <client>Solved Cube Limited</client> is not mentioned on the document

                Within this <document-transaction></document-transaction> section, you must produce the following two sections:
                <thinking>
                    Here you must think step-by-step and justify which one of the document transaction categories are the most applicable to this document,
                    based on the entire context of the document, the guidelines above and your experience as a bookkeeper.
                    You should consider all the information provided and create a concrete argument for your classification.
                    DO THIS STEP BY STEP.
                </thinking>
                <document-transaction-category>
                    The final document transaction category and its name alone go here.
                </document-transaction-category>
            </document-transaction>
        </document>
        <invoice-details>
            <date>
                NOTE: You should adjust the formatting of the date based on detected currency
                or region of the invoice. For example, if you see pound sterling signs,
                you output the date in British date format (DD/MM/YYY), if you were to see US dollar signs,
                you should output the date in American date format (MM/DD/YYYY), etc.
                1. The date of the invoice (if present) in this format: YYYY-MM-DD
                2. If there is no invoice date, set the date to 01/01/2024
            </date>
            <due-date>
                NOTE: You should adjust the formatting of the date based on detected currency
                or region of the invoice. For example, if you see pound sterling signs,
                you output the date in British date format (DD/MM/YYY), if you were to see US dollar signs,
                you should output the date in American date format (MM/DD/YYYY), etc.
                1. The due date of the invoice (if present) in this format: YYYY-MM-DD.
                2. If this is NOT present, then check if there is a note somewhere which
                specifies that it's 30 days or however much from the invoice date.
                3. If there is no written description of the due date, then set the
                due date to be 30 days after <date></date>
                4. If there is no <date></date>, then set the due-date to be 30/01/2024
            </due-date>
            <number>
                1. The invoice number (if present)
                2. If not, then fill this section with a reference section instead
                3. Failing that, just fill this section in with INV0001
            </number>
            <reference>
                A general description of what the invoice covers.
                - INSTEAD OF WRITING "&", JUST WRITE THE WORD AND INSTEAD? THANKS MATE
            </reference>
            <currency>
                1. Three letter currency code goes here (e.g USD, GBP, EUR, JPY, etc.)
                2. If it's unrecognisable, default to GBP
            </currency>
            <totals>
                <total-amount>The total amount of the invoice, including tax and discounts</total-amount>
                <net-amount>The net amount of the invoice, excluding tax and discounts</net-amount>
                <tax-amount>The total tax amount for the entire invoice</tax-amount>
            </totals>

            <account>
                Within this <account></account> section, you must produce the following two sections:
                <thinking>
                    Here you must think step-by-step and justify which one of the account codes are the most applicable to this document,
                    based on the entire context of the document.
                    If <document-transaction-category>SALE</document-transaction-category>, then you must ONLY consider these <account-type></account-type>s:
                        - Revenue
                    If <document-transaction-category>COST</document-transaction-category>, then you must ONLY consider these <account-type></account-type>s:
                        - Direct Costs
                        - Overhead
                        - Expense
                        - Current Asset
                        - Inventory
                        - Fixed Asset
                        - Current Liability
                        - Non-current Liability
                        - Current Liability
                        - Equity

                    You MUST include the following in your thinking process:
                    Relevant <account-description></account-description> section and <account-name></account-name> section which,
                    along with the context of the the entire document and experience as a bookkeeper to fully justify the classification.
                    You should consider all the information provided and create a concrete argument for your classification.
                    DO THIS STEP BY STEP.
                </thinking>
                <account-code>
                    The final account code classification NUMBER ONLY must go here.
                </account-code>
            </account>
            
        </invoice-details>
        <invoice-paid>
            If the document clearly states than an amount has been paid, then this should be
            TRUE, otherwise IT SHOULD BE FALSE IN ALL OTHER CIRCUMSTANCES. THE PRIORITY HERE ARE
            TRUE POSITIVES.
        </invoice-paid>
        <invoice-company>
            1. The name of the company, IF IT IS CLEARLY STATED ON THE INVOICE.
            2. If it is NOT clearly stated, leave this as "Unknown".
        </invoice-company>
        <confidence-score>
            The confidence score of the invoice, between 0 and 1.
        </confidence-score>
    </details>
</instructions>

Here is an example of an output:
<example source_language="english">
    <details>
        <language>English</language>
        <document>
            <document-type>
                <thinking>
                    Step 1: Analyze the document content
                    - The document is titled "TAX INVOICE" at the top.
                    - It contains an "Invoice Number" (INV-9167).
                    - There's a "VAT Number" listed (243119335).
                    - It includes a breakdown of services with quantity, unit price, and VAT amount.
                    - There's a subtotal, VAT total, and final total amount.
                    - It specifies a due date for payment.

                    Step 2: Consider the characteristics of an invoice

                    - Invoices typically state an amount owed from one party to another.
                    - This document clearly shows an amount due (£105.00) from Code Verse Studio Ltd to Neon Numbers Limited.
                    - It provides payment details, including bank account information for settling the invoice.

                    Step 3: Compare with receipt characteristics
                    - While this document does contain financial information, it is not detailing money already spent on a purchase.
                    - It is requesting payment for services rendered, not confirming a completed transaction.

                    Step 4: Evaluate against "OTHER" category

                    - This document doesn't fit into the "OTHER" category as it can be clearly identified as an invoice.
                    - It contains all the typical elements of an invoice: invoice number, VAT details, itemized charges, and payment instructions.

                    Step 5: Conclusion
                    - Based on the content and structure of the document, as well as the guidelines provided, this document is clearly an INVOICE. It contains all the necessary elements of an invoice, including an amount owed, invoice number, VAT details, and payment instructions.

                </thinking>
                <document-type-category>INVOICE<document-type-category>
            </document-type>

            <document-transaction>
                <thinking>
                    Step 1: Document type
                    - We've already established that this is an INVOICE.
                    
                    Step 2: Parties involved
                    - The invoice is from: Neon Numbers Limited
                    - The invoice is to: Code Verse Studio Ltd

                    Step 3: Nature of the transaction
                    - The service provided is "Vat registration"
                    - Neon Numbers Limited is billing Code Verse Studio Ltd for this service


                    Step 4: Relationship to Solved Cube Limited
                    - Solved Cube Limited is not mentioned in this document
                    - Neither Neon Numbers Limited nor Code Verse Studio Ltd is Solved Cube Limited

                    Step 5: Applying the classification criteria
                    - The document type is "INVOICE", which meets the criteria for either SALE or COST
                    - Solved Cube Limited is not involved in this transaction
                    - There are two different companies listed (Neon Numbers Limited and Code Verse Studio Ltd)
                    - The transaction is clear: one company (Neon Numbers) is billing another (Code Verse Studio) for a service

                    Step 6: Considering the classification instructions
                    - This is not a SALE for Solved Cube Limited, as they are not involved
                    - This could be considered a COST from the perspective of Code Verse Studio Ltd
                    - However, the instructions state that if it's ambiguous whether it's a cost or a sale, and Solved Cube Limited is not involved, it should be classified as COST

                    Step 7: Conclusion
                    - Given these considerations, even though this document represents a sale from Neon Numbers Limited's perspective, the classification instructions guide us to categorize it as a COST. 
                    - This is because Solved Cube Limited is not involved, and in such cases where the perspective is ambiguous (i.e., it's not clear whose books we're considering), we are instructed to default to COST.

                </thinking>
                <document-transaction-category>COST<document-transaction-category>
            </document-type>

        </document>
        <invoice-details>
            <date>2024-05-07</date>
            <due-date>2024-06-07</due-date>
            <number>INV-9167</number>
            <reference>VAT registration</reference>
            <currency>GBP</currency>
            <totals>
                <total-amount>105.00</total-amount>
                <net-amount>87.50</net-amount>
                <tax-amount>17.50</tax-amount>                
            </totals>
            <account>
                <thinking>
                    Step 0: We are processing a <document-transaction-category>COST</document-transaction-category> and should therefore only consider <account-type></account-type>s which are relevant to them
                    Step 1: Analyze the line item description "Vat registration".
                    Step 2: Consider the context of the entire invoice, which is for VAT registration services.
                    Step 3: Review the available account codes and descriptions.
                    Step 4: The most relevant account appears to be 401 - Audit and Accountancy fees.
                    Step 5: The account description states "Expenses incurred relating to accounting and audit fees".
                    Step 6: VAT registration is an accounting-related service typically provided by accountants.
                    Step 7: Therefore, classifying this under Audit and Accountancy fees is the most appropriate choice.
                </thinking>
                <account-code>401</account-code>
            </account>
        </invoice-details>
        <invoice-paid>FALSE</invoice-paid>
        <invoice-company>Neon Numbers Limited</invoice-company>
        <confidence-score>0.95</confidence-score>
    </details>
</example>

<task>
YOU MUST CONTINUE THE OUTPUT BY INFILLING FROM THE CONTEXT GIVEN.
DO NOT PRODUCE ANY PREAMBLE, THE TEXT HAS BEEN SET OUT FOR YOU TO COMPLETE,
GIVEN THE ABOVE INSTRUCTIONS. YOU MUST PRODUCE VALID XML CODE WHICH CAN BE
DIRECTLY INTERPRETED BY A PYTHON FUNCTION WHICH CAN READ THE OUTPUT DIRECTLY.
ENSURE ALL NUMERICAL DATA IS ACCURATE AND CONSISTENT ACROSS THE DOCUMENT.
</task>

<details>"""

# def validate_xml(xml_string: str):
#     try:
#         escaped_xml = html.escape(xml_string)
#         etree.fromstring(xml_string)
#         return True
#     except etree.XMLSyntaxError as e:
#         print(f"Invalid XML: {e}")
#         return False

def xml_to_json(xml_string: str):
    def extract_content(tag, text, default=""):
        pattern = rf"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else default

    def safe_float(value, default="0.0"):
        try:
            return float(value)
        except ValueError:
            return default

    # Extract document-transaction-category directly
    document_type = extract_content("document-transaction-category", xml_string, default="UNKNOWN")

    # Parse the rest of the structure
    parsed = {
        "language": extract_content("language", xml_string),
        "invoice-details": {
            "date": extract_content("date", xml_string),
            "due-date": extract_content("due-date", xml_string),
            "number": extract_content("number", xml_string),
            "reference": extract_content("reference", xml_string),
            "currency": extract_content("currency", xml_string),
            "totals": {
                "total-amount": extract_content("total-amount", xml_string),
                "net-amount": extract_content("net-amount", xml_string),
                "tax-amount": extract_content("tax-amount", xml_string),
            },
            "account": {
                "thinking": extract_content("thinking", extract_content("account", xml_string)),
                "accountCode": extract_content("account-code", extract_content("account", xml_string)),
            },
        },
        "invoice-paid": extract_content("invoice-paid", xml_string),
        "invoice-company": extract_content("invoice-company", xml_string),
        "confidence-score": extract_content("confidence-score", xml_string),
    }
    
    # Debug print
    print("Parsed structure:", json.dumps(parsed, indent=2))
    print("Extracted document type:", document_type)

    # Construct the final JSON structure
    json_data = {
        "details": {
            "language": parsed["language"],
            "documentType": document_type,
            "invoiceDetails": {
                "date": parsed["invoice-details"]["date"],
                "dueDate": parsed["invoice-details"]["due-date"],
                "number": parsed["invoice-details"]["number"],
                "reference": parsed["invoice-details"]["reference"],
                "currency": parsed["invoice-details"]["currency"],
                "totals": {
                    "totalAmount": safe_float(parsed["invoice-details"]["totals"]["total-amount"]),
                    "netAmount":   safe_float(parsed["invoice-details"]["totals"]["net-amount"]),
                    "taxAmount":   safe_float(parsed["invoice-details"]["totals"]["tax-amount"]),
                },
                "account": parsed["invoice-details"]["account"],
            },
            "invoicePaid": parsed["invoice-paid"].upper() == "TRUE",
            "invoiceCompany": parsed["invoice-company"],
            "confidenceScore": safe_float(parsed["confidence-score"])
        }
    }

    # Debug print
    print("Extracted JSON data:", json.dumps(json_data, indent=2))

    return json.dumps(json_data, indent=2)

class Scanner:
    def __init__(self, base_dir: str, force_use_bedrock: bool = False):
        """
        A class for scanning and processing documents using OCR and AI analysis.

        This class provides functionality to scan documents, process them using
        Optical Character Recognition (OCR), and analyze them using AI models
        (Claude or Bedrock Claude).

        Attributes:
            base_dir (str): The base directory for document files.
            force_use_bedrock (bool): Flag to force the use of Bedrock Claude.

        Methods:
            scan(fi: str, clientName: str) -> str:
                Scans and processes a document, returning the AI analysis output.
        """
        self.base_dir = base_dir
        self.force_use_bedrock = force_use_bedrock
    
    async def scan(self, fi: str, clientName: str):
        """
        Scan and process a document using OCR and AI analysis.

        This method takes a file path and client name, processes the document
        using Optical Character Recognition (OCR), and then analyzes it using
        an AI model (Claude or Bedrock Claude as a fallback).

        Args:
            fi (str): The file path of the document to be scanned, relative to the base directory.
            clientName (str): The name of the client associated with the document.

        Returns:
            str: The processed and analyzed output from the AI model.

        Raises:
            Exception: If both Claude and Bedrock Claude API calls fail.

        Note:
            This method first attempts to use the regular Claude model. If that fails,
            it falls back to using Bedrock Claude. The method prints status messages
            to indicate which model is being used and any failures that occur.
        """
        if not clientName:
            raise ValueError("Client name cannot be empty.")
            
        file_path = str(Path(self.base_dir) / Path(fi))

        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        prompt = OCR_PROMPT(clientName)
        
        if self.force_use_bedrock:
            try:
                # Use Bedrock Claude directly if force_use_bedrock is True
                o = await bedrock_claude(prompt, file_path, temperature=0)
            except Exception as e:
                print(f"Bedrock Claude call failed: {str(e)}")
                raise  # Re-raise the exception if Bedrock Claude fails
        else:
            try:
                # First, try with the regular Claude model
                o = await claude(prompt, file_path, temperature=0)
            except Exception as e:
                print(f"Regular Claude call failed: {str(e)}. Falling back to Bedrock Claude.")
                try:
                    # If regular Claude fails, try with Bedrock Claude
                    o = await bedrock_claude(prompt, file_path, temperature=0)
                except Exception as e:
                    print(f"Bedrock Claude call also failed: {str(e)}")
                    raise  # Re-raise the exception if both attempts fail

        print("PURE SCANNER OUT:\n", o)
        return o