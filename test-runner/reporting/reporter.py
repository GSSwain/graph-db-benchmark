import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List
from .cost_estimator import CostEstimator

class BenchmarkReporter:
    def __init__(
        self,
        output_dir: str = "reports",
        neo4j_license_usd_per_core_month: float = 0.0,
        html_output_dir: str = "docs",
    ):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.html_output_dir = html_output_dir
        os.makedirs(self.html_output_dir, exist_ok=True)
        self.cost_estimator = CostEstimator(neo4j_license_usd_per_core_month)

    def generate_reports(self, results: Dict[str, Dict[int, Dict[str, Any]]], config: Any, scale_preset: str = "dev"):
        ts_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # 0. Cost Estimations
        target_qps = max(100.0, config.concurrency * 250.0)
        monthly_costs = self.cost_estimator.estimate_monthly_infra_cost(preset_key=scale_preset, target_qps=target_qps)
        cost_per_hop = self.cost_estimator.compute_cost_per_hop_matrix(results, preset_key=scale_preset)

        # 1. Generate the performance summary and separate cost summary
        json_path = os.path.join(self.output_dir, "benchmark_summary.json")
        cost_json_path = os.path.join(self.output_dir, "cost_summary.json")
        summary_data = {
            "timestamp": ts_str,
            "specification": "LDBC FinBench Transaction Workload",
            "scale_preset": scale_preset,
            "concurrency": config.concurrency,
            "tested_hops": config.hops,
            "query_languages": list(results.keys()),
            "results": results
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        with open(cost_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": ts_str,
                "scale_preset": scale_preset,
                "target_qps": target_qps,
                "pricing_scope": "Dedicated database infrastructure only (excluding client runners)",
                "monthly_infrastructure_usd": monthly_costs,
                "cost_per_million_queries_by_hop": cost_per_hop
            }, f, indent=2)

        # 2. Generate the performance CSV log
        csv_path = os.path.join(self.output_dir, "benchmark_summary.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "QueryLanguage", "HopDepth", "Queries", "QPS",
                "p50_ms", "p90_ms", "p95_ms", "p99_ms", "Max_ms", "Errors"
            ])
            for engine, hop_data in results.items():
                for hop, m in hop_data.items():
                    writer.writerow([
                        engine, hop, m.get("count", 0), m.get("qps", 0),
                        m.get("p50_ms", 0), m.get("p90_ms", 0),
                        m.get("p95_ms", 0), m.get("p99_ms", 0), m.get("max_ms", 0),
                        m.get("error_count", 0)
                    ])

        # 3. Generate the performance report
        html_path = os.path.join(self.html_output_dir, "benchmark_report.html")
        template_path = os.path.join(os.path.dirname(__file__), "templates", "report_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        colors = {
            "Neo4j-Cypher": "#008cc1",
            "Neo4j-DirectedTrail": "#38bdf8",
            "Neo4j-APOC": "#1d4ed8",
            "Memcached-MultiGet": "#10b981",
            "Memcached-DFS": "#84cc16",
            "Neptune-Gremlin": "#f59e0b",
            "Neptune-openCypher": "#ea580c",
            "Neptune-SPARQL": "#f43f5e",
            "Spanner-ISO-GQL": "#4285f4",
            "Spanner-Relational-SQL": "#6366f1",
            "Cosmos-Gremlin": "#a855f7",
            "Cosmos-SQL": "#7c3aed"
        }

        # Build the separate cost report
        cost_cards = []
        cost_card_colors = {
            "Neo4j": "#008cc1",
            "Memcached": "#10b981",
            "Neptune": "#f59e0b",
            "Spanner": "#4285f4",
            "CosmosDB": "#a855f7"
        }
        for eng_name, c_info in monthly_costs.items():
            acc_color = cost_card_colors.get(eng_name, "#38bdf8")
            license_detail = ""
            if "license_monthly_usd" in c_info:
                license_detail = (
                    f'<div class="cost-stat-sub">Infrastructure: ${c_info["infrastructure_monthly_usd"]:,.2f}/mo; '
                    + (f'license: ${c_info["license_monthly_usd"]:,.2f}/mo</div>'
                       if c_info["license_usd_per_core_month"] > 0
                       else 'license not priced (quote required)</div>')
                )
            card_html = (
                f'<div class="cost-stat-card" style="--card-accent: {acc_color};">'
                f'  <div class="cost-stat-title">{eng_name} Infrastructure</div>'
                f'  <div class="cost-stat-value">${c_info["monthly_cost_usd"]:,.2f}<span style="font-size: 0.9rem; font-weight: normal; color: #94a3b8;">/mo</span></div>'
                f'  <div class="cost-stat-sub">${c_info["hourly_cost_usd"]:.4f}/hr &bull; {c_info["spec"]}</div>'
                f'{license_detail}'
                f'</div>'
            )
            cost_cards.append(card_html)

        # Build Cost Table Rows
        cost_table_rows = []
        for eng_name, c_info in monthly_costs.items():
            cost_per_1m = (c_info["hourly_cost_usd"] / (3600.0 * target_qps)) * 1_000_000.0
            pricing_unit = self.cost_estimator.catalog.get(eng_name.lower(), {}).get("pricing_unit", "Compute + Storage")
            license_cell = "N/A"
            if "license_monthly_usd" in c_info:
                license_cell = (
                    f'${c_info["license_monthly_usd"]:,.2f}/mo'
                    if c_info["license_usd_per_core_month"] > 0
                    else "Quote required"
                )
            row = (
                f'<tr>'
                f'  <td><strong>{eng_name}</strong></td>'
                f'  <td class="metric-value" style="color: var(--accent);">${c_info["monthly_cost_usd"]:,.2f} / month</td>'
                f'  <td class="metric-value">${c_info["hourly_cost_usd"]:.4f} / hour</td>'
                f'  <td class="metric-value" style="color: var(--success);">${cost_per_1m:.4f}</td>'
                f'  <td>{pricing_unit}</td>'
                f'  <td style="color: var(--text-muted);">{c_info["spec"]}</td>'
                f'  <td class="metric-value">{license_cell}</td>'
                f'</tr>'
            )
            cost_table_rows.append(row)

        cost_template_path = os.path.join(os.path.dirname(__file__), "templates", "cost_report_template.html")
        with open(cost_template_path, "r", encoding="utf-8") as f:
            cost_template = f.read()
        cost_html = cost_template.replace("__TIMESTAMP__", ts_str)
        cost_html = cost_html.replace("__SCALE_PRESET__", scale_preset)
        cost_html = cost_html.replace("__TARGET_QPS__", f"{target_qps:,.0f}")
        cost_html = cost_html.replace("__COST_CARDS_HTML__", "\n".join(cost_cards))
        cost_html = cost_html.replace("__COST_TABLE_ROWS__", "\n".join(cost_table_rows))
        cost_html_path = os.path.join(self.html_output_dir, "cost_report.html")
        with open(cost_html_path, "w", encoding="utf-8") as f:
            f.write(cost_html)

        modeling_template_path = os.path.join(os.path.dirname(__file__), "templates", "modeling_report_template.html")
        with open(modeling_template_path, "r", encoding="utf-8") as f:
            modeling_template = f.read()
        modeling_html = modeling_template.replace("__TIMESTAMP__", ts_str)
        modeling_html_path = os.path.join(self.html_output_dir, "modeling_report.html")
        with open(modeling_html_path, "w", encoding="utf-8") as f:
            f.write(modeling_html)

        all_hops = config.hops
        hop_labels = [str(h) + (" Hop" if h == 1 else " Hops") for h in all_hops]

        latency_datasets = []
        qps_datasets = []
        engine_names = list(results.keys())
        engine_p50 = []
        engine_p99 = []
        table_rows = []

        for eng in engine_names:
            c = colors.get(eng, "#818cf8")
            lat_points = []
            qps_points = []
            eng_data = results[eng]

            for h in all_hops:
                m = eng_data.get(h, {})
                lat_points.append(m.get("p50_ms", 0.0))
                qps_points.append(m.get("qps", 0.0))

                row_html = (
                    "<tr>"
                    + f'<td><span class="engine-badge" style="background:{c}; color:white;">{eng}</span></td>'
                    + f'<td class="metric-value">{h}</td>'
                    + f'<td class="metric-value">{m.get("count", 0)}</td>'
                    + f'<td class="metric-value">{m.get("qps", 0.0):.1f}</td>'
                    + f'<td class="metric-value" style="color: var(--accent);">{m.get("p50_ms", 0.0):.3f}</td>'
                    + f'<td class="metric-value">{m.get("p90_ms", 0.0):.3f}</td>'
                    + f'<td class="metric-value" style="color: var(--danger);">{m.get("p99_ms", 0.0):.3f}</td>'
                    + f'<td class="metric-value">{m.get("max_ms", 0.0):.3f}</td>'
                    + f'<td class="metric-value">{m.get("error_count", 0)}</td>'
                    + "</tr>"
                )
                table_rows.append(row_html)

            latency_datasets.append({
                "label": eng + " p50 (ms)",
                "data": lat_points,
                "borderColor": c,
                "backgroundColor": c,
                "tension": 0.2
            })
            qps_datasets.append({
                "label": eng + " QPS",
                "data": qps_points,
                "backgroundColor": c
            })

            p50_list = [eng_data[h].get("p50_ms", 0.0) for h in all_hops if h in eng_data]
            p99_list = [eng_data[h].get("p99_ms", 0.0) for h in all_hops if h in eng_data]
            engine_p50.append(round(sum(p50_list) / max(1, len(p50_list)), 2))
            engine_p99.append(round(sum(p99_list) / max(1, len(p99_list)), 2))

        chart_data_json = json.dumps({
            "hop_labels": hop_labels,
            "engine_names": engine_names,
            "latency_datasets": latency_datasets,
            "qps_datasets": qps_datasets,
            "engine_p50": engine_p50,
            "engine_p99": engine_p99
        })

        html_out = template.replace("__TIMESTAMP__", ts_str)
        html_out = html_out.replace("__CONCURRENCY__", str(config.concurrency))
        html_out = html_out.replace("__TABLE_ROWS__", "\n".join(table_rows))
        html_out = html_out.replace("__CHART_DATA_JSON__", chart_data_json)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_out)

        print("\n==> Reports successfully generated in " + self.output_dir + ":")
        print("    - Performance HTML Report: " + html_path)
        print("    - Cost HTML Report: " + cost_html_path)
        print("    - Modeling & Storage Report: " + modeling_html_path)
        print("    - Performance JSON Summary: " + json_path)
        print("    - Cost JSON Summary: " + cost_json_path)
        print("    - Performance CSV Summary: " + csv_path)

    def print_terminal_summary(self, results: Dict[str, Dict[int, Dict[str, Any]]]):
        print("\n" + "=" * 105)
        print("         LDBC FINBENCH MULTI-QUERY-LANGUAGE HOP BENCHMARK SUMMARY")
        print("=" * 105)
        header = (
            "Query Language".ljust(22) + " | "
            + "Hops".ljust(5) + " | "
            + "Ops".ljust(5) + " | "
            + "QPS".ljust(8) + " | "
            + "p50 (ms)".ljust(10) + " | "
            + "p90 (ms)".ljust(10) + " | "
            + "p99 (ms)".ljust(10) + " | "
            + "Cost/1M".ljust(10) + " | "
            + "Errors".ljust(6)
        )
        print(header)
        print("-" * 105)
        cost_per_hop = self.cost_estimator.compute_cost_per_hop_matrix(results, preset_key="dev")
        for engine, hop_data in results.items():
            for hop, m in sorted(hop_data.items()):
                c_1m = cost_per_hop.get(engine, {}).get(hop, 0.0)
                line = (
                    engine.ljust(22) + " | "
                    + str(hop).ljust(5) + " | "
                    + str(m.get("count", 0)).ljust(5) + " | "
                    + str(round(m.get("qps", 0.0), 1)).ljust(8) + " | "
                    + str(round(m.get("p50_ms", 0.0), 3)).ljust(10) + " | "
                    + str(round(m.get("p90_ms", 0.0), 3)).ljust(10) + " | "
                    + str(round(m.get("p99_ms", 0.0), 3)).ljust(10) + " | "
                    + f"${c_1m:.3f}".ljust(10) + " | "
                    + str(m.get("error_count", 0)).ljust(6)
                )
                print(line)
            print("-" * 105)
