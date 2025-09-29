"""
Cargo truck data extraction module using structured Gemini output
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .client import GeminiClient
from .schemas import CargoTruckData, Location, TimeWindow, CargoDetails, Coordinates, CargoType
from .attachment_processor import AttachmentProcessor

logger = logging.getLogger(__name__)


class CargoDataExtractor:
    """Extracts structured cargo truck data from emails and attachments"""

    def __init__(self, gemini_client: GeminiClient):
        """Initialize extractor with Gemini client"""
        self.client = gemini_client
        self.attachment_processor = AttachmentProcessor(gemini_client)

    def extract_cargo_data(self, email_data: Dict[str, Any], classification_result: Any) -> Optional[CargoTruckData]:
        """
        Extract cargo truck data from email and attachments

        Args:
            email_data: Email data dictionary
            classification_result: Email classification result

        Returns:
            CargoTruckData object or None if extraction fails
        """
        start_time = time.time()

        try:
            # Process attachments first
            attachments = email_data.get('attachments', [])
            attachment_results = None

            if attachments:
                logger.debug(f"Processing {len(attachments)} attachments for data extraction")
                attachment_results = self.attachment_processor.process_attachments(attachments, email_data)

            # Prepare content for extraction
            content = self._prepare_extraction_content(email_data, attachment_results)

            # Extract structured data using Gemini
            extracted_data = self._extract_structured_data(content, email_data)

            if extracted_data:
                # Calculate extraction time
                extraction_time = time.time() - start_time
                extracted_data.extraction_timestamp = datetime.now()
                extracted_data.source_files = self._get_source_files(attachment_results)
                logger.info(f"Successfully extracted cargo data in {extraction_time:.2f}s")
                return extracted_data
            else:
                logger.warning("Failed to extract structured cargo data")
                return None

        except Exception as e:
            logger.error(f"Failed to extract cargo data: {e}")
            return None

    def _prepare_extraction_content(self, email_data: Dict[str, Any], attachment_results: Optional[Dict[str, Any]]) -> str:
        """Prepare content for cargo data extraction"""
        content_parts = []

        # Add email metadata
        content_parts.append("=== EMAIL METADATA ===")
        content_parts.append(f"Subject: {email_data.get('subject', '')}")
        content_parts.append(f"From: {email_data.get('from', '')}")
        content_parts.append(f"Date: {email_data.get('date_str', '')}")
        content_parts.append(f"Snippet: {email_data.get('snippet', '')}")

        # Add attachment analysis if available
        if attachment_results and attachment_results.get('processed_files'):
            content_parts.append("\n=== ATTACHMENT ANALYSIS ===")
            for processed_file in attachment_results['processed_files']:
                filename = processed_file.get('filename', 'unknown')
                mime_type = processed_file.get('mime_type', 'unknown')
                content_parts.append(f"File: {filename} ({mime_type})")

                # Get analysis for this attachment
                file_obj = processed_file.get('file_obj')
                if file_obj:
                    analysis = self.attachment_processor.analyze_attachment_content(
                        file_obj, email_data, filename
                    )
                    if analysis.get('analysis_performed'):
                        content_parts.append("Analysis:")
                        content_parts.append(analysis.get('analysis_result', ''))
                    elif analysis.get('extracted_text'):
                        content_parts.append("Extracted Text:")
                        content_parts.append(analysis.get('extracted_text', ''))

        return "\n\n".join(content_parts)

    def _extract_structured_data(self, content: str, email_data: Dict[str, Any]) -> Optional[CargoTruckData]:
        """Extract structured data using Gemini with JSON schema"""
        try:
            # Define the JSON schema for structured extraction
            extraction_schema = {
                "type": "OBJECT",
                "properties": {
                    "order_id": {"type": "STRING"},
                    "customer_name": {"type": "STRING"},
                    "loading_location": {
                        "type": "OBJECT",
                        "properties": {
                            "address": {"type": "STRING"},
                            "city": {"type": "STRING"},
                            "state": {"type": "STRING"},
                            "postal_code": {"type": "STRING"},
                            "country": {"type": "STRING"},
                            "coordinates": {
                                "type": "OBJECT",
                                "properties": {
                                    "latitude": {"type": "NUMBER"},
                                    "longitude": {"type": "NUMBER"}
                                }
                            },
                            "facility_name": {"type": "STRING"},
                            "contact_info": {"type": "STRING"}
                        },
                        "required": ["address"]
                    },
                    "loading_time": {
                        "type": "OBJECT",
                        "properties": {
                            "start_date": {"type": "STRING"},
                            "end_date": {"type": "STRING"},
                            "start_time": {"type": "STRING"},
                            "end_time": {"type": "STRING"},
                            "timezone": {"type": "STRING"},
                            "is_flexible": {"type": "BOOLEAN"}
                        },
                        "required": ["start_date"]
                    },
                    "unloading_location": {
                        "type": "OBJECT",
                        "properties": {
                            "address": {"type": "STRING"},
                            "city": {"type": "STRING"},
                            "state": {"type": "STRING"},
                            "postal_code": {"type": "STRING"},
                            "country": {"type": "STRING"},
                            "coordinates": {
                                "type": "OBJECT",
                                "properties": {
                                    "latitude": {"type": "NUMBER"},
                                    "longitude": {"type": "NUMBER"}
                                }
                            },
                            "facility_name": {"type": "STRING"},
                            "contact_info": {"type": "STRING"}
                        },
                        "required": ["address"]
                    },
                    "unloading_time": {
                        "type": "OBJECT",
                        "properties": {
                            "start_date": {"type": "STRING"},
                            "end_date": {"type": "STRING"},
                            "start_time": {"type": "STRING"},
                            "end_time": {"type": "STRING"},
                            "timezone": {"type": "STRING"},
                            "is_flexible": {"type": "BOOLEAN"}
                        },
                        "required": ["start_date"]
                    },
                    "cargo_details": {
                        "type": "OBJECT",
                        "properties": {
                            "cargo_type": {
                                "type": "STRING",
                                "enum": ["general", "perishable", "hazardous", "fragile", "oversized", "temperature_controlled", "liquid", "bulk"]
                            },
                            "description": {"type": "STRING"},
                            "weight_kg": {"type": "NUMBER"},
                            "volume_cbm": {"type": "NUMBER"},
                            "dimensions": {"type": "OBJECT"},
                            "special_requirements": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "is_dangerous": {"type": "BOOLEAN"},
                            "temperature_requirements": {"type": "STRING"}
                        },
                        "required": ["cargo_type", "description"]
                    },
                    "vehicle_requirements": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "special_instructions": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "contact_person": {"type": "STRING"},
                    "contact_phone": {"type": "STRING"},
                    "contact_email": {"type": "STRING"},
                    "priority": {"type": "STRING"},
                    "estimated_duration_hours": {"type": "NUMBER"},
                    "distance_km": {"type": "NUMBER"},
                    "extraction_confidence": {"type": "NUMBER"}
                },
                "required": ["loading_location", "loading_time", "unloading_location", "unloading_time", "cargo_details"]
            }

            # Create extraction prompt
            prompt = f"""
Extract structured cargo truck and logistics information from the following email content.

CONTENT:
---
{content}
---

Instructions:
1. Extract all available cargo truck and logistics information
2. Focus on loading/unloading locations, times, and cargo details
3. Provide confidence score (0.0-1.0) for the extraction accuracy
4. If information is not available, use null or empty values
5. Use standardized formats (YYYY-MM-DD for dates, HH:MM for times)
6. For coordinates, provide latitude/longitude if available or infer from addresses
7. Classify cargo type appropriately

Return the data in the specified JSON format.
"""

            # Generate structured content
            structured_data = self.client.generate_structured_content(prompt, extraction_schema)

            # Convert to CargoTruckData object
            return self._convert_to_cargo_truck_data(structured_data, email_data)

        except Exception as e:
            logger.error(f"Failed to extract structured data: {e}")
            return None

    def _convert_to_cargo_truck_data(self, raw_data: Dict[str, Any], email_data: Dict[str, Any]) -> CargoTruckData:
        """Convert raw extracted data to CargoTruckData object"""
        try:
            # Convert locations
            loading_location = self._convert_to_location(raw_data.get('loading_location', {}))
            unloading_location = self._convert_to_location(raw_data.get('unloading_location', {}))

            # Convert time windows
            loading_time = self._convert_to_time_window(raw_data.get('loading_time', {}))
            unloading_time = self._convert_to_time_window(raw_data.get('unloading_time', {}))

            # Convert cargo details
            cargo_details_dict = raw_data.get('cargo_details', {})
            cargo_type = self._convert_to_cargo_type(cargo_details_dict.get('cargo_type', 'general'))
            cargo_details = CargoDetails(
                cargo_type=cargo_type,
                description=cargo_details_dict.get('description', ''),
                weight_kg=cargo_details_dict.get('weight_kg'),
                volume_cbm=cargo_details_dict.get('volume_cbm'),
                dimensions=cargo_details_dict.get('dimensions'),
                special_requirements=cargo_details_dict.get('special_requirements', []),
                is_dangerous=cargo_details_dict.get('is_dangerous', False),
                temperature_requirements=cargo_details_dict.get('temperature_requirements')
            )

            # Create CargoTruckData object
            cargo_data = CargoTruckData(
                order_id=raw_data.get('order_id'),
                customer_name=raw_data.get('customer_name'),
                loading_location=loading_location,
                loading_time=loading_time,
                unloading_location=unloading_location,
                unloading_time=unloading_time,
                cargo_details=cargo_details,
                vehicle_requirements=raw_data.get('vehicle_requirements', []),
                special_instructions=raw_data.get('special_instructions', []),
                contact_person=raw_data.get('contact_person'),
                contact_phone=raw_data.get('contact_phone'),
                contact_email=raw_data.get('contact_email'),
                priority=raw_data.get('priority'),
                estimated_duration_hours=raw_data.get('estimated_duration_hours'),
                distance_km=raw_data.get('distance_km'),
                extraction_confidence=raw_data.get('extraction_confidence', 0.5),
                extraction_timestamp=datetime.now(),
                source_files=[]
            )

            return cargo_data

        except Exception as e:
            logger.error(f"Failed to convert raw data to CargoTruckData: {e}")
            raise

    def _convert_to_location(self, location_data: Dict[str, Any]) -> Location:
        """Convert raw location data to Location object"""
        try:
            coordinates_data = location_data.get('coordinates', {})
            coordinates = None

            if coordinates_data:
                coordinates = Coordinates(
                    latitude=coordinates_data.get('latitude'),
                    longitude=coordinates_data.get('longitude'),
                    address=coordinates_data.get('address'),
                    confidence=coordinates_data.get('confidence')
                )

            return Location(
                address=location_data.get('address', ''),
                city=location_data.get('city'),
                state=location_data.get('state'),
                postal_code=location_data.get('postal_code'),
                country=location_data.get('country'),
                coordinates=coordinates,
                facility_name=location_data.get('facility_name'),
                contact_info=location_data.get('contact_info')
            )

        except Exception as e:
            logger.error(f"Failed to convert location data: {e}")
            return Location(address="Unknown")

    def _convert_to_time_window(self, time_data: Dict[str, Any]) -> TimeWindow:
        """Convert raw time data to TimeWindow object"""
        try:
            return TimeWindow(
                start_date=time_data.get('start_date', ''),
                end_date=time_data.get('end_date'),
                start_time=time_data.get('start_time'),
                end_time=time_data.get('end_time'),
                timezone=time_data.get('timezone'),
                is_flexible=time_data.get('is_flexible', False)
            )

        except Exception as e:
            logger.error(f"Failed to convert time window data: {e}")
            return TimeWindow(start_date='')

    def _convert_to_cargo_type(self, cargo_type_str: str) -> CargoType:
        """Convert string to CargoType enum"""
        try:
            return CargoType(cargo_type_str.lower().replace(' ', '_'))
        except ValueError:
            logger.warning(f"Unknown cargo type: {cargo_type_str}, defaulting to general")
            return CargoType.GENERAL

    def _get_source_files(self, attachment_results: Optional[Dict[str, Any]]) -> List[str]:
        """Get list of source files used for extraction"""
        if not attachment_results:
            return []

        source_files = []
        for processed_file in attachment_results.get('processed_files', []):
            filename = processed_file.get('filename', 'unknown')
            source_files.append(filename)

        return source_files

    def batch_extract_cargo_data(self, emails_with_classifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract cargo data from multiple emails in batch

        Args:
            emails_with_classifications: List of dictionaries with email_data and classification

        Returns:
            List of extraction results
        """
        results = []

        for i, item in enumerate(emails_with_classifications):
            try:
                email_data = item.get('email_data', {})
                classification = item.get('classification')

                logger.info(f"Extracting cargo data from email {i+1}/{len(emails_with_classifications)}")

                extracted_data = self.extract_cargo_data(email_data, classification)

                results.append({
                    'email_id': email_data.get('id'),
                    'email_subject': email_data.get('subject', 'Unknown'),
                    'extracted_data': extracted_data,
                    'success': extracted_data is not None,
                    'processing_time': time.time() - item.get('start_time', time.time())
                })

            except Exception as e:
                logger.error(f"Failed to extract cargo data from email {i+1}: {e}")
                results.append({
                    'email_id': item.get('email_data', {}).get('id', 'unknown'),
                    'email_subject': item.get('email_data', {}).get('subject', 'Unknown'),
                    'extracted_data': None,
                    'success': False,
                    'error': str(e)
                })

        successful_extractions = sum(1 for r in results if r['success'])
        logger.info(f"Batch extraction completed: {successful_extractions}/{len(results)} successful")

        return results

    def cleanup(self):
        """Clean up resources"""
        try:
            self.attachment_processor.cleanup_temp_files()
        except Exception as e:
            logger.error(f"Failed to cleanup extractor resources: {e}")