/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillStart, useRef } from "@odoo/owl";

export class AccountReport extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.reportRef = useRef("report");
        
        onWillStart(async () => {
            const { report_id } = this.env.searchModel.context;
            if (report_id) {
                this.report = await this.orm.call(
                    "account.report",
                    "get_report_data",
                    [report_id]
                );
            }
        });
    }

    async onFilterChange(event) {
        const { name, value } = event.target;
        await this.updateReport({ [name]: value });
    }

    async onUnfoldAll() {
        await this.updateReport({ unfold_all: true });
    }

    async onFoldAll() {
        await this.updateReport({ unfold_all: false });
    }

    async updateReport(options) {
        const { report_id } = this.env.searchModel.context;
        if (report_id) {
            this.report = await this.orm.call(
                "account.report",
                "get_report_data",
                [report_id],
                { options }
            );
            this.render();
        }
    }

    formatMonetary(amount, currency) {
        if (!amount) return "";
        const formatter = new Intl.NumberFormat(this.env.lang || "en-US", {
            style: "currency",
            currency: currency.name,
            minimumFractionDigits: currency.decimal_places,
            maximumFractionDigits: currency.decimal_places,
        });
        return formatter.format(amount);
    }

    getLineClass(line) {
        const classes = [`level-${line.level}`];
        if (line.unfoldable) classes.push("unfoldable");
        if (line.unfolded) classes.push("unfolded");
        return classes.join(" ");
    }

    async onLineClick(line) {
        if (line.unfoldable) {
            await this.updateReport({
                unfolded_lines: line.unfolded
                    ? this.report.unfolded_lines.filter((id) => id !== line.id)
                    : [...this.report.unfolded_lines, line.id],
            });
        }
    }

    async onExportPdf() {
        const { report_id } = this.env.searchModel.context;
        if (report_id) {
            await this.action.doAction({
                type: "ir.actions.report",
                report_type: "qweb-pdf",
                report_name: "base_accounting_kit_16.report_financial",
                report_file: "base_accounting_kit_16.report_financial",
                data: {
                    report_id,
                    options: this.report.options,
                },
            });
        }
    }

    async onExportXlsx() {
        const { report_id } = this.env.searchModel.context;
        if (report_id) {
            await this.action.doAction({
                type: "ir.actions.report",
                report_type: "xlsx",
                report_name: "base_accounting_kit_16.report_financial.xlsx",
                report_file: "base_accounting_kit_16.report_financial.xlsx",
                data: {
                    report_id,
                    options: this.report.options,
                },
            });
        }
    }
}

AccountReport.template = "base_accounting_kit_16.AccountReport";
AccountReport.props = {
    ...standardFieldProps,
};

registry.category("views").add("account_report", {
    component: AccountReport,
});
