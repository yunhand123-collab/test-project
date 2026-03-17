# 旺店通库存同步 - 部署指南

## 修改文件: `/www/wwwroot/stock-alert-dashboard/wdt_sync.py`

### 改动 1: 添加 `sync_stock()` 函数

在 `sync_cost()` 函数后面，`sync_sales()` 前面，添加：

```python
def sync_stock():
    log.info("拉取全量实时库存...")
    rows = fetch_all(CLIENT_OT, 'stock.search', {})
    if not rows:
        log.error("未拉取到库存数据")
        return None
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
    return save_xlsx(stock_list, f"{UPLOAD_DIR}/stock/auto_{datetime.now().strftime('%Y%m%d')}.xlsx")
```

### 改动 2: 修改 `main()` 函数

在 `update_system('sales', sync_sales())` 后面添加一行：

```python
update_system('stock', sync_stock())
```

### 改动 3: 确保上传目录存在

```bash
mkdir -p /www/wwwroot/stock-alert-dashboard/uploads/stock
```

## 测试

```bash
cd /www/wwwroot/stock-alert-dashboard
python3 -c "from wdt_sync import *; print(fetch_all(CLIENT_OT, 'stock.search', {}, page_size=5))"
```

先用小 page_size 测试接口是否正常返回数据。

## 注意事项

- 如果 `stock.search` 接口报错，可能需要换成 `wms.stock.search` 或 `stock.query.search`
- 旺店通不同版本的 API 方法名可能略有不同
- 建议先在终端手动测试确认接口名和返回字段
