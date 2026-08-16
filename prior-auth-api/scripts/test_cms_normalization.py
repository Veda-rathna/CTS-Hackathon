import os
import sys
import json
import httpx
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cms_client import CMSCoverageClient
from app.repositories.mock.policy_repository import MockPolicyRepository
from app.schemas.policy import PolicyMatch

def test_normalization():
    print("Initializing CMS Coverage Client...")
    client = CMSCoverageClient()
    
    # Let's test with a valid Document ID: e.g., L39054
    doc_id = "L39054"
    hcpcs = "64483"
    print(f"\n1. Querying CMS API for Document ID: {doc_id}")
    try:
        response = client.get_document(doc_id)
        
        if not response or not response.get("data"):
            print("No data found from CMS API.")
            
            # For demonstration, let's mock a realistic CMS JSON response
            response = {
                "data": [
                    {
                        "articleId": "A12345",
                        "articleTitle": "Billing and Coding: Epidural Steroid Injections",
                        "lcdId": "L39054",
                        "effectiveDate": "2023-01-01T00:00:00Z",
                        "status": "ACTIVE"
                    }
                ]
            }
        else:
            print(f"Received raw data from CMS: {json.dumps(response['data'][:1], indent=2)}")
            
        print("\n2. Normalizing CMS response into PolicyMatch...")
        
        # We take the first result to normalize
        cms_item = response["data"][0]
        
        # Extract fields (safely handling potential missing fields based on CMS schemas)
        print("CMS Item Keys:", cms_item.keys())
        article_id = cms_item.get("articleId") or cms_item.get("article_id")
        lcd_id = cms_item.get("lcdId") or cms_item.get("lcd_id") or str(cms_item.get("lcd_version", {}).get("lcd_id", ""))
        # if lcd_id is still missing, maybe it's just 'id' or we can force it to doc_id
        if not lcd_id and doc_id.startswith("L"):
            lcd_id = doc_id
            
        title = cms_item.get("articleTitle", "CMS Retrieved Policy") or cms_item.get("title")
        
        # Parse date
        eff_date_str = cms_item.get("effectiveDate") or cms_item.get("effective_date") or cms_item.get("orig_det_eff_date")
        eff_date = None
        if eff_date_str:
            try:
                eff_date = date.fromisoformat(eff_date_str.split("T")[0])
            except ValueError:
                eff_date = date.today() # fallback
            
        # Create normalized PolicyMatch
        policy = PolicyMatch(
            policy_type="LCD" if lcd_id else "ARTICLE",
            policy_id=str(lcd_id or article_id),
            title=title,
            article_id=str(article_id) if article_id else None,
            jurisdiction_id=None,  # CMS lookup for jurisdiction would be a secondary call
            effective_date=eff_date,
            end_date=None,
            effective=True
        )
        
        print(f"Normalized PolicyMatch object: {policy}")
        
        print("\n3. Upserting into local database (cache)...")
        repo = MockPolicyRepository()
        
        # Check before upsert
        initial_policies = repo.find_policies_for_procedure(hcpcs)
        print(f"Local repo initially has {len(initial_policies)} policies for {hcpcs}.")
        
        # Upsert
        repo.upsert_policy(policy, source="CMS_MCD")
        print(f"Successfully upserted {policy.policy_id} into MockPolicyRepository.")
        
        # We would also need to update the _HCPCS_TO_POLICY_IDX mapping in the mock repo
        # to properly demonstrate the link, but since upsert_policy just adds it to _POLICIES
        # we can verify it's in the full list.
        from app.repositories.mock.policy_repository import _POLICIES
        found = next((p for p in _POLICIES if p.policy_id == policy.policy_id), None)
        if found:
            print(f"Verified {found.policy_id} is in the database!")
            
    except Exception as e:
        print(f"Error during CMS API lookup: {e}")

if __name__ == "__main__":
    test_normalization()
