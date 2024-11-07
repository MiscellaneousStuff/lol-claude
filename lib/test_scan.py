# Standard library imports
import pytest
import asyncio
import json
import logging
import os
from pathlib import Path
from difflib import SequenceMatcher

# Local imports
from lib.llm import gpt, claude, bedrock_claude
from lib.scan import Scanner, xml_to_json
from lib.xero_codes import JSON_CODES, XML_CODES

# Get the absolute path to the core directory
CORE_DIR = Path(__file__).parent.parent.absolute()
TESTING_DIR = CORE_DIR / "testing"

testing_documents = {
    "asterisk": {
        "filename": "asterisk.pdf"
    },
    "heif_img": {
        "filename": "heif_img.heif"
    },
    "capital": {
        "filename": "CAPITAL.PDF"
    },
}

@pytest.fixture(scope="class")
def scanner():
    return Scanner(base_dir=TESTING_DIR)

def similarity_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

def extract_key_elements(result):
    # Parse the JSON string to a dictionary
    data = json.loads(result)
    return {
        "language": data["details"]["language"],
        "documentType": data["details"]["documentType"],
        "totalAmount": data["details"]["invoiceDetails"]["totals"]["totalAmount"],
        "accountCode": data["details"]["invoiceDetails"]["account"]["account-code"]
    }

class TestAsteriskScan:
    @pytest.mark.asyncio
    async def test_valid_scan(self, scanner):
        file_path = testing_documents["asterisk"]["filename"]
        client_name = "Test Client"

        full_file_path = TESTING_DIR / file_path
        assert full_file_path.exists(), f"File does not exist at {full_file_path}"

        invoice = await scanner.scan(fi=file_path, clientName=client_name)
        assert invoice, "Scan should return a non-empty result"

        json_output = xml_to_json(invoice)
        assert isinstance(json_output, str), "Output should be a string"
        assert json_output, "Output should not be empty"

        parsed_json = json.loads(json_output)
        assert "details" in parsed_json, "Output should contain 'details' key"
        assert "language" in parsed_json["details"], "Output should contain 'language' field"
        assert "documentType" in parsed_json["details"], "Output should contain 'documentType' field"

    @pytest.mark.asyncio
    async def test_invalid_file_path(self, scanner):
        with pytest.raises(FileNotFoundError) as excinfo:
            await scanner.scan(fi="non_existent_file.pdf", clientName="Test Client")
        assert "does not exist" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_empty_client_name(self, scanner):
        file_path = testing_documents["asterisk"]["filename"]
        with pytest.raises(ValueError) as excinfo:
            await scanner.scan(fi=file_path, clientName="")
        assert "Client name cannot be empty" in str(excinfo.value)

    @pytest.mark.parametrize("invalid_xml", [
        "<invalid>",
        "<root><unclosed>",
        "Not XML at all",
        "<details><language>English</language><missing_closing_tag>",
        "",
    ])
    def test_xml_to_json_invalid_input(self, invalid_xml):
        result = xml_to_json(invalid_xml)
        parsed_result = json.loads(result)

        # Check if the result has the expected structure even with invalid input
        assert "details" in parsed_result
        assert "language" in parsed_result["details"]
        assert "documentType" in parsed_result["details"]
        assert "invoiceDetails" in parsed_result["details"]

        # Check if default values are used for missing or invalid data
        assert parsed_result["details"]["language"] in ["", "English"]
        assert parsed_result["details"]["documentType"] == "UNKNOWN"  # Changed to "unknown"
        assert parsed_result["details"]["invoiceDetails"]["totals"]["totalAmount"] == "0.0"
        assert float(parsed_result["details"]["confidenceScore"]) == 0.0

    def test_xml_to_json_partial_valid_input(self):
        partial_xml = """
        <details>
            <language>French</language>
            <invoice-details>
                <date>2024-01-01</date>
            </invoice-details>
        </details>
        """
        result = xml_to_json(partial_xml)
        parsed_result = json.loads(result)
        
        assert parsed_result["details"]["language"] == "French"
        assert parsed_result["details"]["invoiceDetails"]["date"] == "2024-01-01"
        assert parsed_result["details"]["documentType"] == "UNKNOWN"  # Changed to "unknown"
        assert parsed_result["details"]["invoiceDetails"]["totals"]["totalAmount"] == "0.0"  # Missing in input
    
    @pytest.mark.asyncio
    async def test_force_use_bedrock_integration(self):
        bedrock_scanner = Scanner(base_dir=TESTING_DIR, force_use_bedrock=True)
        regular_scanner = Scanner(base_dir=TESTING_DIR, force_use_bedrock=False)
        
        file_path = testing_documents["asterisk"]["filename"]
        client_name = "Test Client"

        # Perform multiple runs
        num_runs = 3
        bedrock_results = []
        regular_results = []

        for _ in range(num_runs):
            bedrock_results.append(await bedrock_scanner.scan(fi=file_path, clientName=client_name))
            regular_results.append(await regular_scanner.scan(fi=file_path, clientName=client_name))

        # Compare key elements
        for bedrock_result, regular_result in zip(bedrock_results, regular_results):
            bedrock_elements = extract_key_elements(bedrock_result)
            regular_elements = extract_key_elements(regular_result)

            # Assert that key elements are different
            assert bedrock_elements != regular_elements, "Key elements should differ between Bedrock and regular results"

        # Check similarity within each model's results
        bedrock_similarities = [similarity_ratio(bedrock_results[0], result) for result in bedrock_results[1:]]
        regular_similarities = [similarity_ratio(regular_results[0], result) for result in regular_results[1:]]

        # Assert high similarity within each model's results
        assert all(sim > 0.95 for sim in bedrock_similarities), "Bedrock results should be highly similar across runs"
        assert all(sim > 0.95 for sim in regular_similarities), "Regular results should be highly similar across runs"

        # Compare structural elements
        for bedrock_result, regular_result in zip(bedrock_results, regular_results):
            bedrock_json = json.loads(bedrock_result)
            regular_json = json.loads(regular_result)

            assert set(bedrock_json.keys()) == set(regular_json.keys()), "JSON structure should be the same"
            assert set(bedrock_json["details"].keys()) == set(regular_json["details"].keys()), "Details structure should be the same"

        print("Bedrock results:", bedrock_results)
        print("Regular results:", regular_results)
    
    @pytest.mark.asyncio
    async def test_heif_image_support(self):
        scanner = Scanner(base_dir=TESTING_DIR)
        
        # Valid HEIF image test
        valid_heif_path = os.path.join(TESTING_DIR, "heif_img.heif")
        client_name = "Test Client"
        
        try:
            result = await scanner.scan(fi=valid_heif_path, clientName=client_name)
            
            # Convert XML to JSON
            json_result = xml_to_json(result)
            parsed_result = json.loads(json_result)
            
            assert "details" in parsed_result
            assert "language" in parsed_result["details"]
            assert "documentType" in parsed_result["details"]
            assert "invoiceDetails" in parsed_result["details"]
            
            # Add more specific assertions based on expected content of the HEIF image
            assert parsed_result["details"]["language"], "Language should not be empty"
            assert parsed_result["details"]["documentType"], "Document type should not be empty"
            assert parsed_result["details"]["invoiceDetails"]["totals"]["totalAmount"], "Total amount should not be empty"
            
        except Exception as e:
            pytest.fail(f"Valid HEIF image test failed: {str(e)}")

        # Invalid HEIF image test
        invalid_heif_path = os.path.join(TESTING_DIR, "invalid_heif_image.heic")
        
        with pytest.raises(Exception) as excinfo:
            await scanner.scan(fi=invalid_heif_path, clientName=client_name)
        
        assert "Unable to process HEIF image" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_capital_file_extension(self):
        scanner = Scanner(base_dir=TESTING_DIR)
        
        # Test file with capital PDF extension
        capital_pdf_path = os.path.join(TESTING_DIR, testing_documents["capital"]["filename"])
        client_name = "Test Client"
        
        try:
            result = await scanner.scan(fi=capital_pdf_path, clientName=client_name)
            
            # Convert XML to JSON
            json_result = xml_to_json(result)
            parsed_result = json.loads(json_result)
            
            assert "details" in parsed_result
            assert "language" in parsed_result["details"]
            assert "documentType" in parsed_result["details"]
            assert "invoiceDetails" in parsed_result["details"]
            
            # Add more specific assertions based on expected content of the PDF
            assert parsed_result["details"]["language"], "Language should not be empty"
            assert parsed_result["details"]["documentType"], "Document type should not be empty"
            assert parsed_result["details"]["invoiceDetails"]["totals"]["totalAmount"], "Total amount should not be empty"
            
        except Exception as e:
            pytest.fail(f"Capital PDF extension test failed: {str(e)}")