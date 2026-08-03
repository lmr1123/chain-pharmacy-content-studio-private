# 外部/业务原料暂存（非生产库）

本目录存放 **尚未晋升** 为生产 master 的原料。  
`scripts/query_production_library.py` **不得**默认扫描本目录。

## 通道

| 目录 | 通道 | 谁投放 | 说明 |
| --- | --- | --- | --- |
| `company_authorized/` | A | **业务** | 真包装、Logo、说明书、证据；制作只整理不替代生成 |
| `licensed/` | B | 采购/制作 | 已购商用包 + 同目录 `license.txt` |
| `open_source/` | B | 制作 | 开源矢量/图标 + 许可证副本 |
| `reference_only/` | C | 制作研究 | 结构参考；**禁止**晋升 master 像素 |

## 晋升路径

```text
_intake →（适配贴 series）→ assets/component-library/**/candidates
       → 四轨审核 → master + registry 回写
```

## 真包装政策

真包装与品牌标识 **只接受业务提供的授权原图**。  
不得用素材站「相似包装」或 AI 仿包装填充生产槽位。

## 命名建议

```text
company_authorized/<theme_id-or-sku>/<role>-<date>.{png,jpg,pdf}
licensed/<vendor>/<pack_id>/...
open_source/<project>/<id>/...
reference_only/<platform>/<ref_id>/...
```
