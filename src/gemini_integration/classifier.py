"""
Email classification module using Gemini AI
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .client import GeminiClient
from .schemas import EmailClassification, OrderType

logger = logging.getLogger(__name__)


class EmailClassifier:
    """Classifies emails to identify cargo truck orders"""

    def __init__(self, gemini_client: GeminiClient):
        """Initialize classifier with Gemini client"""
        self.client = gemini_client
        self.order_keywords = [
            "cargo", "truck", "shipment", "freight", "delivery", "transport",
            "loading", "unloading", "pickup", "dispatch", "logistics",
            "order", "booking", "reservation", "schedule", "route",
            "driver", "vehicle", "trailer", "container", "pallet",
            "warehouse", "depot", "terminal", "dock", "bay",
            "weight", "dimensions", "volume", "capacity", "load",
            "origin", "destination", "route", "transit", "mileage",
            "invoice", "bill of lading", "POD", "proof of delivery",
            "ETA", "ETD", "arrival", "departure", "timeslot", "appointment"
        ]

    def classify_email(self, email_data: Dict[str, Any]) -> EmailClassification:
        """
        Classify email to determine if it contains a cargo truck order

        Args:
            email_data: Dictionary containing email information (subject, from, body, etc.)

        Returns:
            EmailClassification object with classification results
        """
        start_time = time.time()

        try:
            # Prepare email content for analysis
            email_content = self._prepare_email_content(email_data)

            # Get classification from Gemini
            classification = self._get_gemini_classification(email_content)

            # Enhance classification with keyword analysis
            enhanced_classification = self._enhance_classification(classification, email_content)

            # Calculate processing time
            processing_time = time.time() - start_time
            enhanced_classification.processing_timestamp = datetime.now()

            logger.info(f"Email classified in {processing_time:.2f}s: "
                       f"is_order={enhanced_classification.is_order}, "
                       f"confidence={enhanced_classification.confidence_score:.2f}")

            return enhanced_classification

        except Exception as e:
            logger.error(f"Failed to classify email: {e}")
            return EmailClassification(
                is_order=False,
                confidence_score=0.0,
                reasoning=f"Classification failed due to error: {str(e)}",
                processing_timestamp=datetime.now()
            )

    def _prepare_email_content(self, email_data: Dict[str, Any]) -> str:
        """Prepare email content for Gemini analysis"""
        content_parts = []

        # Add subject
        subject = email_data.get('subject', '')
        if subject:
            content_parts.append(f"Subject: {subject}")

        # Add sender information
        sender = email_data.get('from', '')
        if sender:
            content_parts.append(f"From: {sender}")

        # Add recipients
        to = email_data.get('to', '')
        if to:
            content_parts.append(f"To: {to}")

        # Add body/snippet
        body = email_data.get('snippet', '') or email_data.get('body', '')
        if body:
            content_parts.append(f"Body: {body}")

        # Add attachment information
        attachments = email_data.get('attachments', [])
        if attachments:
            attachment_info = [f"- {att.get('filename', 'unknown')} ({att.get('mime_type', 'unknown')})"
                              for att in attachments]
            content_parts.append(f"Attachments:\n" + "\n".join(attachment_info))

        return "\n\n".join(content_parts)

    def _get_gemini_classification(self, email_content: str) -> EmailClassification:
        """Use Gemini to classify the email"""
        prompt = f"""
You are an expert logistics assistant. Analyze the following email to determine if it contains a cargo truck order or shipment request.

Email content:
---
{email_content}
---

Instructions:
1. Determine if this email contains a cargo truck order, shipment request, or logistics-related booking
2. Consider the following indicators:
   - Keywords related to transportation, shipping, or logistics
   - Requests for vehicle scheduling or pickup/delivery
   - Loading/unloading instructions or appointments
   - Cargo specifications or shipment details
   - Route information or delivery schedules
3. Provide a confidence score (0.0 to 1.0) in your reasoning
4. If it is an order, identify the type (full truck load, less than truckload, express, standard)
5. Explain your reasoning clearly

Respond in this format:
IS_ORDER: [true/false]
CONFIDENCE: [0.0-1.0]
ORDER_TYPE: [full_truck_load/less_than_truckload/express/standard/none]
REASONING: [detailed explanation]
KEYWORDS: [comma-separated list of relevant keywords found]
"""

        try:
            response = self.client.generate_content(prompt)

            if not response or not hasattr(response, 'text'):
                raise Exception("Invalid response from Gemini")

            return self._parse_gemini_response(response.text)

        except Exception as e:
            logger.error(f"Failed to get Gemini classification: {e}")
            return EmailClassification(
                is_order=False,
                confidence_score=0.0,
                reasoning=f"Gemini classification failed: {str(e)}"
            )

    def _parse_gemini_response(self, response_text: str) -> EmailClassification:
        """Parse Gemini's response into EmailClassification object"""
        try:
            lines = response_text.strip().split('\n')
            parsed = {}

            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().upper()
                    value = value.strip()
                    parsed[key] = value

            # Parse boolean values
            is_order = parsed.get('IS_ORDER', '').lower() in ['true', 'yes', '1']

            # Parse confidence score
            try:
                confidence = float(parsed.get('CONFIDENCE', '0.0'))
            except (ValueError, TypeError):
                confidence = 0.0

            # Parse order type
            order_type_str = parsed.get('ORDER_TYPE', 'none').lower()
            order_type = None
            if is_order and order_type_str != 'none':
                try:
                    order_type = OrderType(order_type_str.replace('-', '_'))
                except ValueError:
                    # Default to standard if unknown type
                    order_type = OrderType.STANDARD

            # Parse keywords
            keywords_str = parsed.get('KEYWORDS', '')
            keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()] if keywords_str else []

            return EmailClassification(
                is_order=is_order,
                confidence_score=max(0.0, min(1.0, confidence)),
                order_type=order_type,
                reasoning=parsed.get('REASONING', 'No reasoning provided'),
                detected_keywords=keywords
            )

        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return EmailClassification(
                is_order=False,
                confidence_score=0.0,
                reasoning=f"Response parsing failed: {str(e)}"
            )

    def _enhance_classification(self, classification: EmailClassification, email_content: str) -> EmailClassification:
        """Enhance classification with additional analysis"""
        content_lower = email_content.lower()

        # Check for high-confidence indicators
        high_confidence_indicators = [
            "booking confirmation", "order confirmation", "shipment confirmation",
            "dispatch order", "pickup scheduled", "delivery appointment",
            "loading dock", "unloading bay", "cargo manifest",
            "bill of lading", "shipping label", "freight invoice"
        ]

        # Check for negative indicators
        negative_indicators = [
            "spam", "unsubscribe", "newsletter", "marketing", "promotion",
            "automated response", "out of office", "do not reply",
            "job application", "resume", "cv", "interview"
        ]

        # Adjust confidence based on indicators
        confidence_adjustment = 0.0

        for indicator in high_confidence_indicators:
            if indicator in content_lower:
                confidence_adjustment += 0.1
                classification.detected_keywords.append(indicator)

        for indicator in negative_indicators:
            if indicator in content_lower:
                confidence_adjustment -= 0.2
                classification.detected_keywords.append(indicator)

        # Apply adjustment
        if confidence_adjustment != 0:
            classification.confidence_score = max(0.0, min(1.0, classification.confidence_score + confidence_adjustment))

        # Update reasoning if adjustments were made
        if confidence_adjustment > 0:
            classification.reasoning += " (Enhanced by positive indicators)"
        elif confidence_adjustment < 0:
            classification.reasoning += " (Reduced by negative indicators)"

        # Final threshold check
        if classification.confidence_score < 0.3:
            classification.is_order = False
            classification.reasoning += " (Below confidence threshold)"

        return classification

    def batch_classify(self, emails: list) -> list:
        """Classify multiple emails in batch"""
        results = []
        total_emails = len(emails)

        logger.info(f"Starting batch classification of {total_emails} emails")

        for i, email in enumerate(emails, 1):
            try:
                logger.debug(f"Classifying email {i}/{total_emails}")

                classification = self.classify_email(email)
                results.append({
                    'email_id': email.get('id'),
                    'classification': classification
                })

                # Add small delay to avoid rate limiting
                if i < total_emails:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Failed to classify email {i}: {e}")
                results.append({
                    'email_id': email.get('id'),
                    'classification': EmailClassification(
                        is_order=False,
                        confidence_score=0.0,
                        reasoning=f"Batch classification failed: {str(e)}"
                    )
                })

        successful_classifications = sum(1 for r in results if r['classification'].is_order)
        logger.info(f"Batch classification completed: {successful_classifications}/{total_emails} classified as orders")

        return results