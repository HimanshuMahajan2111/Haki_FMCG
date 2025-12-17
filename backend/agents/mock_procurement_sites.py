"""
Mock Procurement Websites - Realistic RFP data sources

Simulates official procurement portals:
1. eProcure - Government e-Procurement system
2. GEM (Government e-Marketplace)
3. TCS iON Marketplace
4. L&T E-Procurement Portal
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random


class MockProcurementWebsite:
    """Base class for mock procurement websites."""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.rfps = []
    
    def get_rfps(self, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get RFPs from website."""
        filtered = self.rfps
        if category:
            filtered = [rfp for rfp in self.rfps if category.lower() in rfp['category'].lower()]
        return filtered[:limit]


class eProcurePortal(MockProcurementWebsite):
    """Government eProcurement portal simulation."""
    
    def __init__(self):
        super().__init__("eProcure", "https://eprocure.gov.in")
        self._generate_rfps()
    
    def _generate_rfps(self):
        """Generate realistic government RFPs."""
        self.rfps = [
            {
                'rfp_id': 'EPRO-2025-001',
                'title': 'Supply of 11 kV Underground Power Cables for NTPC',
                'buyer': 'NTPC Limited',
                'category': 'Power Cables',
                'description': '''
                NTPC invites bids for supply and installation of 11 kV Underground XLPE cables.
                Total requirement: 5000 meters across 3 locations (Dadri, Faridabad, Unchahar).
                Specifications: 3 Core, 185 sq mm Aluminum conductor, XLPE insulation, PVC sheath.
                Standards: IS 7098 Part 1, IEC 60502-1 compliant.
                ''',
                'estimated_value': 18500000,  # 1.85 Cr
                'quantity': '5000 meters',
                'specifications': {
                    'voltage_rating': '11 kV',
                    'conductor_size': '185 sq mm',
                    'conductor_material': 'Aluminum',
                    'cores': '3',
                    'insulation': 'XLPE',
                    'sheath': 'PVC',
                    'armour': 'SWA',
                    'standards': ['IS 7098', 'IEC 60502-1']
                },
                'publish_date': (datetime.now() - timedelta(days=2)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=28)).isoformat(),
                'location': 'Multiple locations (Delhi NCR, UP)',
                'contact': 'procurement@ntpc.co.in',
                'documents': ['Technical_Specs_11kV_Cable.pdf', 'BOQ_Template.xlsx', 'Terms_Conditions.pdf'],
                'website': 'eprocure.gov.in',
                'bid_type': 'Open Tender',
                'emd_amount': 370000,  # 2% of estimated value
            },
            {
                'rfp_id': 'EPRO-2025-002',
                'title': 'Procurement of Solar DC Cables for 100 MW Solar Plant - SECI',
                'buyer': 'Solar Energy Corporation of India (SECI)',
                'category': 'Solar Cables',
                'description': '''
                SECI requires high-quality solar DC cables for 100 MW solar power project in Rajasthan.
                Total requirement: 50,000 meters of 4 sq mm and 30,000 meters of 6 sq mm solar cables.
                Specifications: Single core, tinned copper conductor, XLPE insulation, UV resistant.
                Must be TUV certified and meet EN 50618 standards.
                ''',
                'estimated_value': 45000000,  # 4.5 Cr
                'quantity': '80000 meters (combined)',
                'specifications': {
                    'voltage_rating': '1.8 kV DC',
                    'conductor_size': '4 sq mm, 6 sq mm',
                    'conductor_material': 'Tinned Copper',
                    'cores': '1',
                    'insulation': 'XLPE',
                    'temperature_rating': '90C',
                    'uv_resistance': 'Required',
                    'certifications': ['TUV', 'BIS', 'IEC 62930'],
                    'standards': ['EN 50618', 'IEC 62930']
                },
                'publish_date': (datetime.now() - timedelta(days=5)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=25)).isoformat(),
                'location': 'Jodhpur, Rajasthan',
                'contact': 'tenders@seci.co.in',
                'documents': ['Solar_Cable_Tech_Specs.pdf', 'Site_Details.pdf', 'BOQ.xlsx'],
                'website': 'eprocure.gov.in',
                'bid_type': 'Limited Tender',
                'emd_amount': 900000,
            },
            {
                'rfp_id': 'EPRO-2025-003',
                'title': 'Railway Signaling Cables Supply - Indian Railways',
                'buyer': 'Indian Railways (CORE)',
                'category': 'Signaling Cables',
                'description': '''
                Supply of railway signaling cables for Eastern Railway zone modernization.
                Requirement: 25,000 meters of 4-pair, 20,000 meters of 8-pair signaling cables.
                Must comply with RDSO specifications and Indian Railway standards.
                ''',
                'estimated_value': 8500000,  # 85 Lakhs
                'quantity': '45000 meters',
                'specifications': {
                    'voltage_rating': '650 V',
                    'conductor_size': '1.5 sq mm',
                    'conductor_material': 'Copper',
                    'pairs': '4-pair, 8-pair',
                    'insulation': 'PVC',
                    'sheath': 'PVC',
                    'certifications': ['RDSO', 'BIS'],
                    'standards': ['IS 1554', 'RDSO Spec M&C/OHE/109']
                },
                'publish_date': (datetime.now() - timedelta(days=7)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=23)).isoformat(),
                'location': 'Kolkata, West Bengal',
                'contact': 'stores@core.indianrailways.gov.in',
                'documents': ['RDSO_Specifications.pdf', 'Technical_Schedule.pdf'],
                'website': 'eprocure.gov.in',
                'bid_type': 'Open Tender',
                'emd_amount': 170000,
            },
            {
                'rfp_id': 'EPRO-2025-004',
                'title': 'LT Power Cables for Smart City Project - Bhopal',
                'buyer': 'Bhopal Smart City Development Corporation',
                'category': 'Power Cables - LT',
                'description': '''
                Supply and laying of LT cables for Bhopal Smart City infrastructure.
                Total: 15,000 meters of 1.1 kV cables (various sizes).
                Part of AMRUT scheme implementation.
                ''',
                'estimated_value': 6200000,  # 62 Lakhs
                'quantity': '15000 meters',
                'specifications': {
                    'voltage_rating': '1.1 kV',
                    'conductor_size': '50-240 sq mm',
                    'conductor_material': 'Aluminum',
                    'cores': '3.5',
                    'insulation': 'PVC/XLPE',
                    'standards': ['IS 1554', 'IS 7098']
                },
                'publish_date': (datetime.now() - timedelta(days=3)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=27)).isoformat(),
                'location': 'Bhopal, Madhya Pradesh',
                'contact': 'procurement@bhopalsmart.in',
                'documents': ['Project_Overview.pdf', 'Cable_Specifications.pdf'],
                'website': 'eprocure.gov.in',
                'bid_type': 'Open Tender',
                'emd_amount': 124000,
            }
        ]


class GEMPortal(MockProcurementWebsite):
    """Government e-Marketplace simulation."""
    
    def __init__(self):
        super().__init__("GEM", "https://gem.gov.in")
        self._generate_rfps()
    
    def _generate_rfps(self):
        """Generate GEM marketplace RFPs."""
        self.rfps = [
            {
                'rfp_id': 'GEM-2025-501',
                'title': 'Flexible Cables for Industrial Plant - BHEL',
                'buyer': 'Bharat Heavy Electricals Limited (BHEL)',
                'category': 'Flexible Cables',
                'description': '''
                BHEL Haridwar unit requires flexible cables for plant maintenance.
                Various sizes: 0.75 to 10 sq mm, 2/3/4 core configurations.
                Total estimated quantity: 20,000 meters.
                ''',
                'estimated_value': 3800000,  # 38 Lakhs
                'quantity': '20000 meters',
                'specifications': {
                    'voltage_rating': '1.1 kV',
                    'conductor_size': '0.75-10 sq mm',
                    'conductor_material': 'Copper',
                    'cores': '2/3/4',
                    'insulation': 'PVC',
                    'flame_retardant': 'FRLS',
                    'standards': ['IS 694']
                },
                'publish_date': (datetime.now() - timedelta(days=1)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=29)).isoformat(),
                'location': 'Haridwar, Uttarakhand',
                'contact': 'stores@bhel.in',
                'documents': ['Material_Requirement.pdf'],
                'website': 'gem.gov.in',
                'bid_type': 'GeM Bidding',
                'emd_amount': 76000,
            },
            {
                'rfp_id': 'GEM-2025-502',
                'title': 'Control Cables for Metro Rail Project - Delhi Metro',
                'buyer': 'Delhi Metro Rail Corporation (DMRC)',
                'category': 'Control Cables',
                'description': '''
                Supply of control and instrumentation cables for Phase 4 expansion.
                Multi-core cables (4-37 cores), shielded and unshielded variants.
                Total requirement: 35,000 meters.
                ''',
                'estimated_value': 12500000,  # 1.25 Cr
                'quantity': '35000 meters',
                'specifications': {
                    'voltage_rating': '1.1 kV',
                    'conductor_size': '1.5 sq mm',
                    'conductor_material': 'Copper',
                    'cores': '4-37 cores',
                    'insulation': 'PVC',
                    'sheath': 'PVC',
                    'shielding': 'Optional',
                    'standards': ['IS 1554', 'BS 5467']
                },
                'publish_date': (datetime.now() - timedelta(days=4)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=26)).isoformat(),
                'location': 'New Delhi',
                'contact': 'procurement@delhimetrorail.com',
                'documents': ['Technical_Specification.pdf', 'QAP.pdf'],
                'website': 'gem.gov.in',
                'bid_type': 'GeM Bidding',
                'emd_amount': 250000,
            },
            {
                'rfp_id': 'GEM-2025-503',
                'title': 'House Wiring Cables Bulk Procurement - CPWD',
                'buyer': 'Central Public Works Department',
                'category': 'House Wiring Cables',
                'description': '''
                Annual rate contract for house wiring cables (0.75-6 sq mm).
                For various government buildings and quarters across Delhi NCR.
                ''',
                'estimated_value': 5600000,  # 56 Lakhs
                'quantity': '50000 meters',
                'specifications': {
                    'voltage_rating': '1.1 kV',
                    'conductor_size': '0.75-6 sq mm',
                    'conductor_material': 'Copper',
                    'cores': '1/2/3',
                    'insulation': 'PVC',
                    'flame_retardant': 'FR',
                    'standards': ['IS 694']
                },
                'publish_date': (datetime.now() - timedelta(days=6)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=24)).isoformat(),
                'location': 'Delhi NCR',
                'contact': 'cpwd.stores@nic.in',
                'documents': ['Rate_Contract_Terms.pdf'],
                'website': 'gem.gov.in',
                'bid_type': 'Rate Contract',
                'emd_amount': 112000,
            }
        ]


class TCSiONMarketplace(MockProcurementWebsite):
    """TCS iON procurement portal simulation."""
    
    def __init__(self):
        super().__init__("TCS iON", "https://ion.tcs.com")
        self._generate_rfps()
    
    def _generate_rfps(self):
        """Generate TCS iON marketplace RFPs."""
        self.rfps = [
            {
                'rfp_id': 'TCS-2025-701',
                'title': 'EPC Project - Solar Power Plant Cabling - Adani Green',
                'buyer': 'Adani Green Energy Limited',
                'category': 'Solar Cables - LSTK',
                'description': '''
                LSTK project for 50 MW solar plant cabling package.
                Includes solar DC cables, AC cables, earthing cables.
                Complete design, supply, installation, testing, and commissioning.
                ''',
                'estimated_value': 65000000,  # 6.5 Cr
                'quantity': 'As per BOQ',
                'specifications': {
                    'dc_cables': '4 sq mm, 6 sq mm - 40,000 meters',
                    'ac_cables': '95-185 sq mm - 5,000 meters',
                    'earthing': '50 sq mm - 10,000 meters',
                    'voltage_rating': '1.8 kV DC, 1.1 kV AC',
                    'certifications': ['TUV', 'IEC 62930', 'BIS'],
                    'standards': ['EN 50618', 'IEC 60502']
                },
                'publish_date': (datetime.now() - timedelta(days=8)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=22)).isoformat(),
                'location': 'Gujarat',
                'contact': 'procurement@adanigreenenergy.com',
                'documents': ['EPC_Scope.pdf', 'Design_Basis.pdf', 'BOQ.xlsx'],
                'website': 'ion.tcs.com',
                'bid_type': 'LSTK/EPC',
                'emd_amount': 1300000,
            },
            {
                'rfp_id': 'TCS-2025-702',
                'title': 'Power Distribution Cables - Tata Power Mumbai',
                'buyer': 'Tata Power Company Limited',
                'category': 'Power Cables',
                'description': '''
                Underground cable network upgrade for Mumbai distribution.
                11 kV and 33 kV XLPE cables required.
                Total: 8,000 meters (11 kV) + 2,000 meters (33 kV).
                ''',
                'estimated_value': 28000000,  # 2.8 Cr
                'quantity': '10000 meters',
                'specifications': {
                    '11kv': '185 sq mm, 3 core, Al conductor',
                    '33kv': '240 sq mm, 3 core, Al conductor',
                    'insulation': 'XLPE',
                    'armour': 'SWA',
                    'standards': ['IS 7098', 'IEC 60502']
                },
                'publish_date': (datetime.now() - timedelta(days=3)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=27)).isoformat(),
                'location': 'Mumbai, Maharashtra',
                'contact': 'scm@tatapower.com',
                'documents': ['Cable_Specs.pdf', 'Installation_Requirements.pdf'],
                'website': 'ion.tcs.com',
                'bid_type': 'Open Tender',
                'emd_amount': 560000,
            }
        ]


class LTEProcurement(MockProcurementWebsite):
    """L&T E-Procurement portal simulation."""
    
    def __init__(self):
        super().__init__("L&T eProcure", "https://eprocure.lntecc.com")
        self._generate_rfps()
    
    def _generate_rfps(self):
        """Generate L&T procurement RFPs."""
        self.rfps = [
            {
                'rfp_id': 'LT-2025-901',
                'title': 'Metro Rail Traction Power Cables - L&T Metro',
                'buyer': 'Larsen & Toubro Limited (Metro Projects)',
                'category': 'Power Cables - Metro',
                'description': '''
                Supply of 25 kV traction power cables for metro rail project.
                High voltage XLPE cables with stringent fire safety requirements.
                Total requirement: 12,000 meters.
                ''',
                'estimated_value': 48000000,  # 4.8 Cr
                'quantity': '12000 meters',
                'specifications': {
                    'voltage_rating': '25 kV',
                    'conductor_size': '300 sq mm',
                    'conductor_material': 'Copper',
                    'cores': '1',
                    'insulation': 'XLPE',
                    'fire_performance': 'Low Smoke Zero Halogen (LSZH)',
                    'standards': ['IEC 60502', 'BS 7846']
                },
                'publish_date': (datetime.now() - timedelta(days=10)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=20)).isoformat(),
                'location': 'Multiple metro projects',
                'contact': 'metro.procurement@lntecc.com',
                'documents': ['Traction_Cable_Specs.pdf', 'Fire_Test_Requirements.pdf'],
                'website': 'eprocure.lntecc.com',
                'bid_type': 'LSTK Package',
                'emd_amount': 960000,
            },
            {
                'rfp_id': 'LT-2025-902',
                'title': 'Industrial Plant Cabling - L&T Construction',
                'buyer': 'Larsen & Toubro Limited (ECC)',
                'category': 'Industrial Cables',
                'description': '''
                Complete cabling package for petrochemical plant.
                Power, control, instrumentation, and earthing cables.
                LSTK scope including design, supply, and installation.
                ''',
                'estimated_value': 125000000,  # 12.5 Cr
                'quantity': 'As per detailed engineering',
                'specifications': {
                    'power_cables': '1.1-11 kV various sizes',
                    'control_cables': 'Multi-core, armoured',
                    'instrumentation': 'Shielded, twisted pair',
                    'flame_retardant': 'Required',
                    'standards': ['IS 1554', 'IS 7098', 'IEC 60502']
                },
                'publish_date': (datetime.now() - timedelta(days=12)).isoformat(),
                'submission_deadline': (datetime.now() + timedelta(days=18)).isoformat(),
                'location': 'Gujarat',
                'contact': 'ecc.scm@lntecc.com',
                'documents': ['Project_Scope.pdf', 'Cable_Schedule.xlsx', 'Technical_Specs.pdf'],
                'website': 'eprocure.lntecc.com',
                'bid_type': 'LSTK/EPC',
                'emd_amount': 2500000,
            }
        ]


def get_all_mock_websites() -> List[MockProcurementWebsite]:
    """Get all mock procurement websites."""
    return [
        eProcurePortal(),
        GEMPortal(),
        TCSiONMarketplace(),
        LTEProcurement()
    ]


def get_all_rfps(category: str = None) -> List[Dict[str, Any]]:
    """Get all RFPs from all mock websites."""
    all_rfps = []
    for website in get_all_mock_websites():
        all_rfps.extend(website.get_rfps(category=category))
    return all_rfps
