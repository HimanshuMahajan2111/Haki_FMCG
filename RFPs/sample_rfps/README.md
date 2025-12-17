# RFP Sample Documents

This directory contains sample RFP documents from various procurement portals.

## Structure

```
sample_rfps/
├── eprocure/          # Government eProcurement portal RFPs
├── gem/               # Government e-Marketplace RFPs
├── tcs_ion/           # TCS iON marketplace RFPs
├── lt_eprocure/       # L&T eProcurement portal RFPs
└── README.md          # This file
```

## Document Format

Each RFP document includes:
- Technical specifications
- Bill of Quantities (BOQ)
- Terms & Conditions
- Submission guidelines
- Contact information

## Sample RFPs Available

### eProcure Portal
1. **EPRO-2025-001**: 11 kV Underground Cables for NTPC (₹1.85 Cr)
2. **EPRO-2025-002**: Solar DC Cables for 100 MW Plant - SECI (₹4.5 Cr)
3. **EPRO-2025-003**: Railway Signaling Cables - Indian Railways (₹85 Lakhs)
4. **EPRO-2025-004**: LT Power Cables - Bhopal Smart City (₹62 Lakhs)

### GEM Portal
1. **GEM-2025-501**: Flexible Cables for BHEL Plant (₹38 Lakhs)
2. **GEM-2025-502**: Control Cables for Delhi Metro (₹1.25 Cr)
3. **GEM-2025-503**: House Wiring Cables - CPWD (₹56 Lakhs)

### TCS iON Marketplace
1. **TCS-2025-701**: Solar Plant Cabling LSTK - Adani Green (₹6.5 Cr)
2. **TCS-2025-702**: Power Distribution Cables - Tata Power (₹2.8 Cr)

### L&T eProcurement
1. **LT-2025-901**: Metro Rail Traction Cables (₹4.8 Cr)
2. **LT-2025-902**: Industrial Plant Cabling LSTK (₹12.5 Cr)

## Processing

All RFPs are automatically scanned and processed by the multi-agent system:
- **Sales Agent**: Extracts requirements and specifications
- **Technical Agent**: Matches products and validates specifications
- **Pricing Agent**: Calculates costs and generates quotes
- **Master Agent**: Coordinates workflow and generates final response

## API Access

Use the `/api/scanner` endpoints to access RFP data programmatically.
