"""
Notion MCP Server 2-Level Nested Page Publisher
------------------------------------------------
Publishes Level 1 (Executive Summary) and Level 2 (Technical Report with AI Warning Banner)
nested hierarchically under the parent container.
"""
import sys
import os
import re
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

def publish_nested_defect_pages(
    short_md_path: str,
    tech_md_path: str,
    defect_id: str,
    short_title: str,
    parent_page_id: str = None
) -> dict:
    parent_page_id = parent_page_id or utils.DEFAULT_PARENT_PAGE_ID
    
    with open(short_md_path, "r", encoding="utf-8") as f:
        short_md = f.read()
        
    with open(tech_md_path, "r", encoding="utf-8") as f:
        tech_md = f.read()

    clean_short_md = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+\)', r'`\1`', short_md)
    clean_tech_md = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+\)', r'`\1`', tech_md)

    page1_id, page1_url = utils.resolve_level1_from_sheet(defect_id)
    if not page1_id:
        page1_id, page1_url = utils.find_notion_level1_page_id(defect_id)
    
    if not page1_id:
        level1_title = f"{defect_id}_{short_title}"
        payload_level1 = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": level1_title,
            "markdown": clean_short_md
        }
        page1 = utils.call_notion_mcp("create_page", payload_level1)
        if not page1:
            raise RuntimeError("Fallo al crear la página Nivel 1 en Notion")
            
        page1_id = page1["id"]
        page1_url = page1.get("url", "").replace("https://app.notion.com/p/", utils.NOTION_PUBLIC_DOMAIN)
    else:
        print(f"Reutilizando página Nivel 1 existente: {page1_url}")
    
    level2_title = f"{defect_id}_{short_title}_tecnico"
    payload_level2 = {
        "parent": {"type": "page_id", "page_id": page1_id},
        "title": level2_title,
        "markdown": clean_tech_md
    }
    
    page2 = utils.call_notion_mcp("create_page", payload_level2)
    page2_url = page2.get("url", "").replace("https://app.notion.com/p/", utils.NOTION_PUBLIC_DOMAIN) if page2 else None
    
    return {
        "level1_id": page1_id,
        "level1_url": page1_url,
        "level2_id": page2["id"] if page2 else None,
        "level2_url": page2_url
    }

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python notion_mcp_publisher.py <short_md_path> <tech_md_path> <defect_id> <short_title> [parent_page_id]")
        sys.exit(1)
        
    res = publish_nested_defect_pages(
        short_md_path=sys.argv[1],
        tech_md_path=sys.argv[2],
        defect_id=sys.argv[3],
        short_title=sys.argv[4],
        parent_page_id=sys.argv[5] if len(sys.argv) > 5 else None
    )
    if res:
        print(json.dumps(res, indent=2))
