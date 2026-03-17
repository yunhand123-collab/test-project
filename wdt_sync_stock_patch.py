#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存同步补丁 - 添加到 wdt_sync.py 中

使用方法：
1. 将 sync_stock() 函数添加到 wdt_sync.py 中（放在 sync_sales() 之前）
2. 在 main() 中添加 update_system('stock', sync_stock()) 调用
"""

# ============================================================
# 步骤 1: 在 wdt_sync.py 中添加以下函数（放在 sync_cost() 后面）
# ============================================================

def sync_stock():
    """
    拉取旺店通全量实时库存数据（含零库存和负库存）
    API: stock.search (库存查询接口)
    分两次拉取确保覆盖全部 SKU：
    1. 默认拉取（库存>0）
    2. 补充拉取负库存（可发货库存<0）
    """
    log.info("拉取全量实时库存...")

    # 第一次：拉取全部（默认返回有库存的）
    rows = fetch_all(CLIENT_OT, 'stock.search', {
        'status': 0,  # 0=全部状态（已启用+未启用）
    })

    # 第二次：补充拉取负库存的 SKU
    log.info("补充拉取负库存SKU...")
    neg_rows = fetch_all(CLIENT_OT, 'stock.search', {
        'status': 0,
        'stock_num_max': 0,  # 库存<=0
    })

    # 合并去重（以 spec_no + warehouse_no 为唯一键）
    seen = set()
    all_rows = []
    for r in (rows or []) + (neg_rows or []):
        key = (r.get('spec_no', ''), r.get('warehouse_no', ''))
        if key not in seen:
            seen.add(key)
            all_rows.append(r)
    rows = all_rows
    log.info(f"合并后总记录数: {len(rows)}（含负库存 {len(neg_rows or [])} 条）")
    if not rows:
        log.error("未拉取到库存数据")
        return None

    # 提取需要的字段
    stock_list = []
    for r in rows:
        stock_list.append({
            '仓库编号': r.get('warehouse_no', ''),
            '仓库名称': r.get('warehouse_name', ''),
            '商家编码': r.get('spec_no', ''),
            '货品编号': r.get('goods_no', ''),
            '货品名称': r.get('goods_name', ''),
            '规格名称': r.get('spec_name', ''),
            '规格码': r.get('spec_code', ''),
            '实际库存': float(r.get('stock_num', 0) or 0),
            '可用库存': float(r.get('usable_num', 0) or 0),
            '锁定库存': float(r.get('order_lock_num', 0) or 0),
            '在途库存': float(r.get('on_road_num', 0) or 0),
            '次品库存': float(r.get('defective_num', 0) or 0),
            '货品类别': r.get('cate_name', ''),
        })

    log.info(f"全量库存 SKU 数: {len(stock_list)}")
    return save_xlsx(
        stock_list,
        f"{UPLOAD_DIR}/stock/auto_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )


# ============================================================
# 步骤 2: 修改 main() 函数，添加库存同步调用
# ============================================================

# 原来的 main():
#   def main():
#       log.info("="*50+f"\n同步开始  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#       update_system('inventory_cost', sync_cost())
#       update_system('sales', sync_sales())
#       log.info(f"同步完成  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"+"="*50)

# 改为:
#   def main():
#       log.info("="*50+f"\n同步开始  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#       update_system('inventory_cost', sync_cost())
#       update_system('sales', sync_sales())
#       update_system('stock', sync_stock())        # <-- 新增
#       log.info(f"同步完成  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"+"="*50)
