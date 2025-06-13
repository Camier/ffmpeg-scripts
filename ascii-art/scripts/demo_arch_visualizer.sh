#!/bin/bash

# =============================================================================
# AsciiSymphony Pro - Architecture Diagram Visualizer Demo
# =============================================================================
# This script demonstrates the Architecture Diagram Visualizer enhancement
# with sample diagrams and guided interactive examples
# =============================================================================

# Source the enhancer
source "$(dirname "$0")/enhance_ascii_visualizer.sh"

# Create temp directory for demo
DEMO_DIR="$(mktemp -d)"
trap 'rm -rf "$DEMO_DIR"' EXIT

# Terminal colors for the demo interface
RED="\033[0;31m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
MAGENTA="\033[0;35m"
CYAN="\033[0;36m"
BOLD="\033[1m"
RESET="\033[0m"

# Demo architecture diagram files
SAMPLE_DIAGRAM="${DEMO_DIR}/sample_architecture.txt"
ENHANCED_DIAGRAM="${DEMO_DIR}/enhanced_architecture.txt"
HTML_DIAGRAM="${DEMO_DIR}/architecture.html"
METADATA_FILE="${DEMO_DIR}/metadata.json"

# =============================================================================
# SAMPLE DIAGRAMS
# =============================================================================

# Create a sample architecture diagram
create_sample_diagram() {
    cat > "$SAMPLE_DIAGRAM" << 'EOD'
[Core Architecture Model]
Knowledge Foundation <-> Creative Engine <-> Validation Matrix

=== I. Systematic Discovery Layer ===

1. Structural Analysis Protocol
- Hybrid traversal algorithms:
  • Technical graph traversal (TGT-2023 spec)
  • Artistic path weighting (APW-7 standards)
- Output maps:
  ┌───────────────────────┬───────────────────────┐
  │ Technical Dependency  │ Creative Influence    │
  │ Graphs                │ Networks              │
  ├───────────────────────┼───────────────────────┤
  │ Cross-Domain          │ Relationship Matrices │
  │ Validation Matrices   │                       │
  └───────────────────────┴───────────────────────┘

2. Information Synthesis Engine
Input Channels:
[Technical Specs] -> SyntaxParser v3.1
[Creative Assets] -> ContextInterpreter v2.4

Validation Gates:
1. Technical Compliance Checkpoint (TCC-9)
2. Creative Consistency Auditor (CCA-5)
3. Cross-Domain Harmony Analyzer (CDHA-3)

=== II. Adaptive Design System ===

Component Interface Standards:
• Technical Contracts:
  - Input validation: RFC-7321
  - Output validation: ISO-2023-7A
• Creative Contracts:
  - Aesthetic compatibility levels (ACL 1-5)
  - Style preservation thresholds (SPT 0.8+)

Implementation Blueprint Phases:
Phase 1: Base Implementation (TCC-9 compliant)
Phase 2: Creative Adaptation Layer (CAL-3)
Phase 3: Harmony Validation Wrapper (HVW-2)

=== III. Validation Matrix ===

Validation Layer Stack:
+----------------+---------------------+-----------------------+
| Layer          | Technical Checks    | Creative Checks       |
+----------------+---------------------+-----------------------+
| Component      | Type safety         | Style consistency     |
|                | Null checks         | Pattern alignment     |
+----------------+---------------------+-----------------------+
| Integration    | Data flow validation| Aesthetic harmony     |
|                | API compliance      | Intent preservation   |
+----------------+---------------------+-----------------------+
| System         | Performance metrics | Creative impact score |
|                | Stability index     | User experience grade |
+----------------+---------------------+-----------------------+

Error Handling Protocol:
Error Classification Matrix:
1. Technical (T-Class):
   - Resolution: Apply T-Mitigation v4
   - Documentation: ERR-T-2023 format

2. Creative (C-Class):
   - Resolution: Initiate C-Revision v2
   - Documentation: ERR-C-2023 format

3. Hybrid (H-Class):
   - Resolution: Cross-Domain Review
   - Documentation: ERR-H-2023 format

=== IV. Implementation Protocol ===

Parameter Control Matrix:
| Parameter Type | Technical Rules         | Creative Guidelines      |
|----------------|-------------------------|--------------------------|
| Core           | RFC-7321 compliant      | ACL 5 required           |
| Adaptive       | ISO-2023-7A standards   | SPT 1.2+ recommended     |
| Experimental   | Draft spec 2023-BETA    | Creative waiver allowed  |

Implementation Roadmap:
1. Initialize Core System (TCC-9 base)
2. Apply Creative Adaptation Layer
3. Install Validation Harness
4. Execute Harmony Verification
5. Deploy Monitoring Agents

=== V. Knowledge Integration ===

Live Correlation Rules:
- Technical Spec Drift: >5% triggers T-Revision
- Creative Alignment: <80% triggers C-Review
- Cross-Domain Sync: Hourly auto-sync

Decision Matrix:
| Tech Certainty | Creative Ambiguity | Action                 |
|----------------|--------------------|------------------------|
| High (90%+)    | Low (<20%)         | Direct implementation  |
| Medium (60-89%)| Moderate (21-50%)  | Prototype + Review     |
| Low (<60%)     | High (>50%)        | Exploration Sprint     |
EOD

    echo "Sample diagram created at: $SAMPLE_DIAGRAM"
}

# =============================================================================
# DEMO FUNCTIONS
# =============================================================================

# Show welcome message
show_welcome() {
    clear
    echo -e "${BOLD}${GREEN}AsciiSymphony Pro - Architecture Diagram Visualizer Demo${RESET}"
    echo -e "${BLUE}====================================================${RESET}"
    echo
    echo -e "This demo will guide you through the capabilities of the Architecture"
    echo -e "Diagram Visualizer enhancement for AsciiSymphony Pro."
    echo
    echo -e "You'll see how it can transform technical ASCII diagrams into"
    echo -e "enhanced, more readable visualizations with semantic highlighting,"
    echo -e "structural improvements, and technical analysis."
    echo
    echo -e "${YELLOW}Press Enter to continue...${RESET}"
    read -r
}

# Show the original diagram
show_original_diagram() {
    clear
    echo -e "${BOLD}${BLUE}Original Architecture Diagram${RESET}"
    echo -e "${BLUE}======================${RESET}"
    echo
    echo -e "${YELLOW}The sample below shows a raw architecture diagram with complex"
    echo -e "technical specifications, tables, and structural elements:${RESET}"
    echo
    cat "$SAMPLE_DIAGRAM"
    echo
    echo -e "${YELLOW}Press Enter to see the enhanced version...${RESET}"
    read -r
}

# Show enhanced diagram - standard mode
show_enhanced_diagram() {
    clear
    echo -e "${BOLD}${GREEN}Enhanced Architecture Diagram${RESET}"
    echo -e "${GREEN}=========================${RESET}"
    echo
    echo -e "${YELLOW}The same diagram with automatic enhancement:${RESET}"
    echo -e "${CYAN}(Using semantic highlighting and double-line box style)${RESET}"
    echo
    
    # Generate enhanced diagram
    process_diagram "$SAMPLE_DIAGRAM" "$ENHANCED_DIAGRAM" "ansi"
    
    # Display the enhanced diagram
    cat "$ENHANCED_DIAGRAM"
    
    echo
    echo -e "${YELLOW}Notice how the tables, headings, and technical specifications"
    echo -e "are highlighted and enhanced for better readability.${RESET}"
    echo
    echo -e "${YELLOW}Press Enter to continue...${RESET}"
    read -r
}

# Demonstrate technical analysis
demonstrate_analysis() {
    clear
    echo -e "${BOLD}${CYAN}Diagram Complexity Analysis${RESET}"
    echo -e "${CYAN}===========================${RESET}"
    echo
    
    # Run complexity analysis
    analyze_diagram_complexity "$SAMPLE_DIAGRAM" > "${DEMO_DIR}/analysis.txt"
    
    # Display analysis results
    cat "${DEMO_DIR}/analysis.txt"
    
    echo
    echo -e "${YELLOW}This analysis shows the complexity level of the diagram and"
    echo -e "provides recommendations for optimal visualization.${RESET}"
    echo
    echo -e "${YELLOW}Press Enter to continue...${RESET}"
    read -r
}

# Demonstrate metadata extraction
demonstrate_metadata() {
    clear
    echo -e "${BOLD}${MAGENTA}Diagram Metadata Extraction${RESET}"
    echo -e "${MAGENTA}============================${RESET}"
    echo
    
    # Extract metadata
    extract_diagram_metadata "$SAMPLE_DIAGRAM" "$METADATA_FILE"
    
    echo -e "${YELLOW}Structural metadata has been extracted from the diagram:${RESET}"
    echo
    
    # Pretty-print the JSON for readability with highlighting
    echo -e "${CYAN}$(grep -E '"diagram_type"|"sections"|"components"|"technical_specs"|"relationships"' "$METADATA_FILE" | 
        sed 's/"diagram_type"/"Diagram Type"/; 
             s/"sections"/"Major Sections"/;
             s/"components"/"Key Components"/;
             s/"technical_specs"/"Technical Standards Referenced"/;
             s/"relationships"/"Relationship Structures"/')${RESET}"
    
    echo
    echo -e "${YELLOW}This metadata can be used by other tools for documentation,"
    echo -e "integration, or further analysis.${RESET}"
    echo
    echo -e "${YELLOW}Press Enter to continue...${RESET}"
    read -r
}

# Demonstrate different visualization modes
demonstrate_visualization_modes() {
    clear
    echo -e "${BOLD}${GREEN}Visualization Modes${RESET}"
    echo -e "${GREEN}===================${RESET}"
    echo
    echo -e "${YELLOW}The enhancer supports different visualization modes and styles.${RESET}"
    echo
    
    # Show different highlight modes
    echo -e "${BOLD}${CYAN}1. Semantic Highlighting${RESET} (focuses on meaning)"
    DIAGRAM_CONFIG[highlight_mode]="semantic"
    DIAGRAM_CONFIG[box_style]="double"
    process_diagram "$SAMPLE_DIAGRAM" "${DEMO_DIR}/semantic.txt" "ansi"
    tail -n 15 "${DEMO_DIR}/semantic.txt" | head -n 10
    echo
    
    echo -e "${BOLD}${CYAN}2. Syntax Highlighting${RESET} (focuses on structure)"
    DIAGRAM_CONFIG[highlight_mode]="syntax"
    DIAGRAM_CONFIG[box_style]="single"
    process_diagram "$SAMPLE_DIAGRAM" "${DEMO_DIR}/syntax.txt" "ansi"
    tail -n 15 "${DEMO_DIR}/syntax.txt" | head -n 10
    echo
    
    echo -e "${BOLD}${CYAN}3. Relation Highlighting${RESET} (focuses on connections)"
    DIAGRAM_CONFIG[highlight_mode]="relation"
    DIAGRAM_CONFIG[box_style]="bold"
    process_diagram "$SAMPLE_DIAGRAM" "${DEMO_DIR}/relation.txt" "ansi"
    tail -n 15 "${DEMO_DIR}/relation.txt" | head -n 10
    echo
    
    echo -e "${BOLD}${CYAN}4. Hybrid Highlighting${RESET} (combines multiple approaches)"
    DIAGRAM_CONFIG[highlight_mode]="hybrid"
    DIAGRAM_CONFIG[box_style]="rounded"
    process_diagram "$SAMPLE_DIAGRAM" "${DEMO_DIR}/hybrid.txt" "ansi"
    tail -n 15 "${DEMO_DIR}/hybrid.txt" | head -n 10
    
    echo
    echo -e "${YELLOW}These different modes can be selected based on the specific"
    echo -e "needs of the viewer or the type of diagram.${RESET}"
    echo
    echo -e "${YELLOW}Press Enter to continue...${RESET}"
    read -r
}

# Demonstrate technical vs creative views
demonstrate_technical_creative() {
    clear
    echo -e "${BOLD}${BLUE}Technical vs Creative Views${RESET}"
    echo -e "${BLUE}=========================${RESET}"
    echo
    echo -e "${YELLOW}The enhancer can generate specialized views optimized for"
    echo -e "either technical precision or creative representation.${RESET}"
    echo
    
    # Technical view
    echo -e "${BOLD}${CYAN}Technical View${RESET} (optimized for precision and detail)"
    enhance_technical_diagram "$SAMPLE_DIAGRAM" "${DEMO_DIR}/technical.txt" "detail"
    tail -n 15 "${DEMO_DIR}/technical.txt" | head -n 10
    echo
    
    # Creative view
    echo -e "${BOLD}${MAGENTA}Creative View${RESET} (optimized for visual appeal and conceptual understanding)"
    enhance_creative_diagram "$SAMPLE_DIAGRAM" "${DEMO_DIR}/creative.txt" "artistic"
    tail -n 15 "${DEMO_DIR}/creative.txt" | head -n 10
    
    echo
    echo -e "${YELLOW}These specialized views can help bridge the gap between"
    echo -e "technical and non-technical stakeholders.${RESET}"
    echo
    echo -e "${YELLOW}Press Enter to continue...${RESET}"
    read -r
}

# Demonstrate HTML export
demonstrate_html_export() {
    clear
    echo -e "${BOLD}${GREEN}HTML Export${RESET}"
    echo -e "${GREEN}===========${RESET}"
    echo
    
    # Generate HTML version
    process_diagram "$SAMPLE_DIAGRAM" "$HTML_DIAGRAM" "html"
    
    echo -e "${YELLOW}The diagram has been exported to HTML format at:${RESET}"
    echo -e "${CYAN}$HTML_DIAGRAM${RESET}"
    echo
    echo -e "${YELLOW}The HTML version provides:${RESET}"
    echo -e "- Clean, stylized presentation with CSS"
    echo -e "- Accessibility-friendly format"
    echo -e "- Semantic highlighting using CSS classes"
    echo -e "- Easy sharing and inclusion in documentation"
    echo
    
    # Show a snippet of the HTML
    echo -e "${BOLD}HTML Snippet:${RESET}"
    head -n 20 "$HTML_DIAGRAM" | grep -v "<!DOCTYPE" | grep -v "<style" | tail -n 10
    echo "..."
    
    echo
    echo -e "${YELLOW}The HTML file can be opened in any web browser"
    echo -e "for improved viewing and sharing.${RESET}"
    echo
    echo -e "${YELLOW}Press Enter to continue...${RESET}"
    read -r
}

# Show summary and usage commands
show_usage_summary() {
    clear
    echo -e "${BOLD}${GREEN}Summary and Usage${RESET}"
    echo -e "${GREEN}=================${RESET}"
    echo
    echo -e "${YELLOW}You've seen the main features of the Architecture Diagram Visualizer!"
    echo -e "Here's a quick reference for using it with your own diagrams:${RESET}"
    echo
    echo -e "${BOLD}Basic Usage:${RESET}"
    echo -e "./enhance_ascii_visualizer.sh [options] input_file [output_file]"
    echo
    echo -e "${BOLD}Common Commands:${RESET}"
    echo -e "${BLUE}# Basic enhancement${RESET}"
    echo -e "./enhance_ascii_visualizer.sh your_diagram.txt enhanced_diagram.txt"
    echo
    echo -e "${BLUE}# Technical view with annotations${RESET}"
    echo -e "./enhance_ascii_visualizer.sh --mode technical --detailed your_diagram.txt"
    echo
    echo -e "${BLUE}# Analyze diagram complexity${RESET}"
    echo -e "./enhance_ascii_visualizer.sh --analyze your_diagram.txt"
    echo
    echo -e "${BLUE}# Extract metadata${RESET}"
    echo -e "./enhance_ascii_visualizer.sh --extract-metadata your_diagram.txt"
    echo
    echo -e "${BLUE}# Generate HTML version${RESET}"
    echo -e "./enhance_ascii_visualizer.sh -f html your_diagram.txt diagram.html"
    echo
    echo -e "${BLUE}# Use creative visualization mode${RESET}"
    echo -e "./enhance_ascii_visualizer.sh --mode creative your_diagram.txt"
    echo
    echo -e "${YELLOW}For full documentation, see README_ENHANCE.md${RESET}"
    echo
    echo -e "${BOLD}${GREEN}Thank you for trying the Architecture Diagram Visualizer!${RESET}"
    echo
    echo -e "${YELLOW}Press Enter to exit...${RESET}"
    read -r
}

# =============================================================================
# MAIN DEMO SEQUENCE
# =============================================================================

main() {
    # Create demo files
    create_sample_diagram
    
    # Run demo sequence
    show_welcome
    show_original_diagram
    show_enhanced_diagram
    demonstrate_analysis
    demonstrate_metadata
    demonstrate_visualization_modes
    demonstrate_technical_creative
    demonstrate_html_export
    show_usage_summary
    
    # Cleanup is handled by the trap
    clear
    echo -e "${GREEN}Demo completed. Generated files were in: $DEMO_DIR${RESET}"
    echo -e "${GREEN}(This directory has been cleaned up)${RESET}"
    echo
}

# Run the demo
main "$@"
