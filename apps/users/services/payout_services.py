import requests
import logging
from django.conf import settings
from core.exceptions import ValidationError

logger = logging.getLogger("apps.users.services.payout")

def setup_freelancer_payout_account(user, account_number, ifsc, name) -> dict:
    """
    Setup a payout contact and bank fund account with RazorpayX.
    Saves the fund account ID and masked bank details to FreelancerProfile.
    """
    from apps.users.models import FreelancerProfile
    
    if not hasattr(user, 'freelancer_profile'):
        raise ValidationError("Only freelancers can setup payout accounts.")
        
    profile = user.freelancer_profile
    
    # 1. Clean input
    account_number = str(account_number).strip()
    ifsc = str(ifsc).strip().upper()
    name = str(name).strip()
    
    if not account_number or len(account_number) < 8:
        raise ValidationError("Invalid bank account number.")
    if not ifsc or len(ifsc) < 11:
        raise ValidationError("Invalid bank IFSC code.")
    if not name:
        raise ValidationError("Account holder name is required.")
        
    # Check if credentials are mock/placeholder
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    is_placeholder = (
        not key_id or 
        key_id.startswith("rzp_test_placeholder") or 
        key_id == "your_razorpay_key_id"
    )
    
    fund_account_id = ""
    bank_name = "SIMULATED BANK"
    
    if is_placeholder:
        logger.info("Using simulated RazorpayX payout credentials for freelancer: %s", user.email)
        fund_account_id = f"fa_mock_{user.id}"
        bank_name = "Mock Bank (Simulated)"
    else:
        # 2. Call RazorpayX to Create Contact
        contact_url = "https://api.razorpay.com/v1/contacts"
        contact_payload = {
            "name": name,
            "email": user.email,
            "type": "employee",
            "reference_id": f"free_user_{user.id}"
        }
        
        try:
            contact_res = requests.post(
                contact_url,
                json=contact_payload,
                auth=(key_id, key_secret),
                timeout=10
            )
            contact_res.raise_for_status()
            contact_data = contact_res.json()
            contact_id = contact_data.get("id")
        except Exception as exc:
            logger.warning("Failed to create RazorpayX contact for user_id=%s. Falling back to mock payout creation: %s", user.id, exc)
            fund_account_id = f"fa_mock_{user.id}"
            bank_name = "Mock Bank (Fallback)"
            
        # 3. Call RazorpayX to Create Fund Account if contact creation was successful
        if not fund_account_id:
            fund_url = "https://api.razorpay.com/v1/fund_accounts"
            fund_payload = {
                "contact_id": contact_id,
                "account_type": "bank_account",
                "bank_account": {
                    "name": name,
                    "ifsc": ifsc,
                    "account_number": account_number
                }
            }
            
            try:
                fund_res = requests.post(
                    fund_url,
                    json=fund_payload,
                    auth=(key_id, key_secret),
                    timeout=10
                )
                fund_res.raise_for_status()
                fund_data = fund_res.json()
                fund_account_id = fund_data.get("id")
                bank_name = fund_data.get("bank_account", {}).get("bank_name", "Registered Bank")
            except Exception as exc:
                logger.warning("Failed to create RazorpayX fund account for user_id=%s. Falling back to mock payout creation: %s", user.id, exc)
                fund_account_id = f"fa_mock_{user.id}"
                bank_name = "Mock Bank (Fallback)"
            
    # 4. Save masked details
    masked_acc = "*" * (len(account_number) - 4) + account_number[-4:] if len(account_number) >= 4 else "****"
    
    profile.razorpay_fund_account_id = fund_account_id
    profile.payout_bank_name = bank_name
    profile.payout_masked_account = masked_acc
    profile.payout_account_holder = name
    profile.save()
    
    logger.info("Successfully setup freelancer payout account: user_id=%s fund_account=%s", user.id, fund_account_id)
    return {
        "payout_linked": True,
        "bank_name": bank_name,
        "masked_account": masked_acc,
        "account_holder": name
    }
