#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成器
为InvestMindPro主项目生成专业的股票分析PDF报告
基于aiagents-stock子项目的pdf_generator.py适配
"""

import io
import os
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """PDF报告生成器"""

    def __init__(self):
        self.chinese_font = self._register_chinese_fonts()
        self.styles = self._create_styles()

    def _register_chinese_fonts(self) -> str:
        """注册中文字体 - 支持Windows和Linux系统"""
        try:
            if 'ChineseFont' in pdfmetrics.getRegisteredFontNames():
                return 'ChineseFont'

            # Windows系统字体路径
            windows_font_paths = [
                'C:/Windows/Fonts/simsun.ttc',
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/msyh.ttf',
            ]

            # Linux系统字体路径（Docker环境）
            linux_font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            ]

            all_font_paths = windows_font_paths + linux_font_paths

            for font_path in all_font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        logger.info(f"成功注册中文字体: {font_path}")
                        return 'ChineseFont'
                    except Exception as e:
                        logger.warning(f"尝试注册字体 {font_path} 失败: {e}")
                        continue

            logger.warning("未找到中文字体，PDF中文可能显示为方框")
            return 'Helvetica'
        except Exception as e:
            logger.error(f"注册中文字体时出错: {e}")
            return 'Helvetica'

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """创建自定义样式"""
        base_styles = getSampleStyleSheet()

        return {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=base_styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1a365d')
            ),
            'subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=base_styles['Normal'],
                fontName=self.chinese_font,
                fontSize=12,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.grey
            ),
            'heading1': ParagraphStyle(
                'CustomHeading1',
                parent=base_styles['Heading2'],
                fontName=self.chinese_font,
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#2c5282')
            ),
            'heading2': ParagraphStyle(
                'CustomHeading2',
                parent=base_styles['Heading3'],
                fontName=self.chinese_font,
                fontSize=14,
                spaceAfter=8,
                spaceBefore=12,
                textColor=colors.HexColor('#2f855a')
            ),
            'heading3': ParagraphStyle(
                'CustomHeading3',
                parent=base_styles['Heading4'],
                fontName=self.chinese_font,
                fontSize=12,
                spaceAfter=6,
                spaceBefore=10,
                textColor=colors.HexColor('#744210')
            ),
            'normal': ParagraphStyle(
                'CustomNormal',
                parent=base_styles['Normal'],
                fontName=self.chinese_font,
                fontSize=10,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                leading=14
            ),
            'small': ParagraphStyle(
                'CustomSmall',
                parent=base_styles['Normal'],
                fontName=self.chinese_font,
                fontSize=9,
                spaceAfter=4,
                textColor=colors.grey
            ),
            'rating_buy': ParagraphStyle(
                'RatingBuy',
                parent=base_styles['Normal'],
                fontName=self.chinese_font,
                fontSize=14,
                textColor=colors.HexColor('#c53030'),
                alignment=TA_CENTER
            ),
            'rating_sell': ParagraphStyle(
                'RatingSell',
                parent=base_styles['Normal'],
                fontName=self.chinese_font,
                fontSize=14,
                textColor=colors.HexColor('#2f855a'),
                alignment=TA_CENTER
            ),
            'rating_hold': ParagraphStyle(
                'RatingHold',
                parent=base_styles['Normal'],
                fontName=self.chinese_font,
                fontSize=14,
                textColor=colors.HexColor('#d69e2e'),
                alignment=TA_CENTER
            ),
        }

    def _create_table_style(self, header_color: str = '#2c5282') -> TableStyle:
        """创建表格样式"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f7fafc'), colors.white]),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ])

    def generate_analysis_report(
        self,
        stock_info: Dict[str, Any],
        analysis_result: Dict[str, Any],
        agents_analysis: Optional[List[Dict[str, Any]]] = None,
        debate_result: Optional[Dict[str, Any]] = None,
        final_decision: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        生成股票分析PDF报告

        Args:
            stock_info: 股票基本信息
            analysis_result: 分析结果
            agents_analysis: 各智能体分析结果列表
            debate_result: 辩论结果
            final_decision: 最终决策

        Returns:
            PDF文件的字节内容
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=30
        )

        story = []

        # 1. 封面/标题
        story.extend(self._build_header(stock_info))

        # 2. 股票基本信息
        story.extend(self._build_stock_info_section(stock_info, analysis_result))

        # 3. 各智能体分析
        if agents_analysis:
            story.extend(self._build_agents_analysis_section(agents_analysis))

        # 4. 辩论结果
        if debate_result:
            story.extend(self._build_debate_section(debate_result))

        # 5. 最终决策
        if final_decision:
            story.extend(self._build_decision_section(final_decision))

        # 6. 风险提示和免责声明
        story.extend(self._build_disclaimer_section())

        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def _build_header(self, stock_info: Dict[str, Any]) -> List:
        """构建报告头部"""
        story = []

        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        stock_name = stock_info.get('name', stock_info.get('stock_name', '未知'))
        stock_code = stock_info.get('code', stock_info.get('stock_code', '未知'))

        story.append(Paragraph("智投顾问团 AI分析报告", self.styles['title']))
        story.append(Paragraph(f"{stock_name} ({stock_code})", self.styles['subtitle']))
        story.append(Paragraph(f"报告生成时间: {current_time}", self.styles['small']))
        story.append(Spacer(1, 30))

        return story

    def _build_stock_info_section(
        self,
        stock_info: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List:
        """构建股票基本信息部分"""
        story = []

        story.append(Paragraph("一、股票基本信息", self.styles['heading1']))

        # 基本信息表格
        basic_data = [
            ['项目', '数值', '项目', '数值'],
            [
                '股票代码',
                stock_info.get('code', stock_info.get('stock_code', 'N/A')),
                '股票名称',
                stock_info.get('name', stock_info.get('stock_name', 'N/A'))
            ],
            [
                '当前价格',
                f"¥{stock_info.get('current_price', stock_info.get('price', 'N/A'))}",
                '涨跌幅',
                f"{stock_info.get('change_percent', stock_info.get('pct_change', 'N/A'))}%"
            ],
            [
                '市盈率(PE)',
                str(stock_info.get('pe_ratio', stock_info.get('pe', 'N/A'))),
                '市净率(PB)',
                str(stock_info.get('pb_ratio', stock_info.get('pb', 'N/A')))
            ],
            [
                '总市值',
                self._format_market_cap(stock_info.get('market_cap', stock_info.get('total_mv', 'N/A'))),
                '流通市值',
                self._format_market_cap(stock_info.get('circ_mv', 'N/A'))
            ],
            [
                '所属行业',
                stock_info.get('industry', 'N/A'),
                '上市日期',
                stock_info.get('list_date', 'N/A')
            ],
        ]

        table = Table(basic_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(self._create_table_style())
        story.append(table)
        story.append(Spacer(1, 20))

        return story

    def _build_agents_analysis_section(self, agents_analysis: List[Dict[str, Any]]) -> List:
        """构建智能体分析部分"""
        story = []

        story.append(Paragraph("二、AI智能体分析", self.styles['heading1']))

        # 智能体名称映射
        agent_icons = {
            'macro_analyst': '🌍 宏观分析师',
            'industry_analyst': '🏭 行业分析师',
            'technical_analyst': '📈 技术分析师',
            'funds_analyst': '💰 资金分析师',
            'fundamental_analyst': '📊 基本面分析师',
            'research_director': '🔬 研究总监',
            'market_director': '📉 市场总监',
            'systemic_risk': '⚠️ 系统风险官',
            'portfolio_risk': '🛡️ 组合风险官',
            'decision_manager': '👔 决策总经理',
        }

        for agent in agents_analysis:
            agent_name = agent.get('agent_name', agent.get('name', '未知智能体'))
            agent_role = agent.get('agent_role', agent.get('role', ''))
            analysis = agent.get('analysis', agent.get('content', '暂无分析'))

            # 获取显示名称
            display_name = agent_icons.get(agent_name, f"🤖 {agent_name}")

            story.append(Paragraph(display_name, self.styles['heading2']))
            if agent_role:
                story.append(Paragraph(f"职责: {agent_role}", self.styles['small']))

            # 处理分析内容
            if isinstance(analysis, dict):
                analysis_text = analysis.get('content', analysis.get('text', str(analysis)))
            else:
                analysis_text = str(analysis)

            # 替换换行符
            analysis_text = analysis_text.replace('\n', '<br/>')
            story.append(Paragraph(analysis_text, self.styles['normal']))
            story.append(Spacer(1, 10))

        return story

    def _build_debate_section(self, debate_result: Dict[str, Any]) -> List:
        """构建辩论结果部分"""
        story = []

        story.append(Paragraph("三、多空辩论", self.styles['heading1']))

        # 多方观点
        bull_view = debate_result.get('bull_view', debate_result.get('bullish', ''))
        if bull_view:
            story.append(Paragraph("🐂 多方观点", self.styles['heading2']))
            bull_text = str(bull_view).replace('\n', '<br/>')
            story.append(Paragraph(bull_text, self.styles['normal']))
            story.append(Spacer(1, 10))

        # 空方观点
        bear_view = debate_result.get('bear_view', debate_result.get('bearish', ''))
        if bear_view:
            story.append(Paragraph("🐻 空方观点", self.styles['heading2']))
            bear_text = str(bear_view).replace('\n', '<br/>')
            story.append(Paragraph(bear_text, self.styles['normal']))
            story.append(Spacer(1, 10))

        # 综合结论
        conclusion = debate_result.get('conclusion', debate_result.get('summary', ''))
        if conclusion:
            story.append(Paragraph("📋 综合结论", self.styles['heading2']))
            conclusion_text = str(conclusion).replace('\n', '<br/>')
            story.append(Paragraph(conclusion_text, self.styles['normal']))

        story.append(Spacer(1, 20))
        return story

    def _build_decision_section(self, final_decision: Dict[str, Any]) -> List:
        """构建最终决策部分"""
        story = []

        story.append(Paragraph("四、投资决策", self.styles['heading1']))

        # 投资评级
        rating = final_decision.get('rating', final_decision.get('recommendation', '持有'))
        rating_style = self.styles['rating_hold']
        if '买' in rating or '增' in rating or 'buy' in rating.lower():
            rating_style = self.styles['rating_buy']
        elif '卖' in rating or '减' in rating or 'sell' in rating.lower():
            rating_style = self.styles['rating_sell']

        story.append(Paragraph(f"投资评级: {rating}", rating_style))
        story.append(Spacer(1, 15))

        # 决策详情表格
        decision_data = [
            ['项目', '内容'],
            ['操作建议', final_decision.get('operation_advice', final_decision.get('action', 'N/A'))],
            ['目标价位', str(final_decision.get('target_price', 'N/A'))],
            ['进场区间', final_decision.get('entry_range', final_decision.get('entry_price', 'N/A'))],
            ['止盈位', str(final_decision.get('take_profit', final_decision.get('profit_target', 'N/A')))],
            ['止损位', str(final_decision.get('stop_loss', 'N/A'))],
            ['持有周期', final_decision.get('holding_period', final_decision.get('time_horizon', 'N/A'))],
            ['仓位建议', final_decision.get('position_size', final_decision.get('position', 'N/A'))],
            ['信心度', f"{final_decision.get('confidence_level', final_decision.get('confidence', 'N/A'))}/10"],
        ]

        table = Table(decision_data, colWidths=[1.5*inch, 4*inch])
        table.setStyle(self._create_table_style('#2f855a'))
        story.append(table)
        story.append(Spacer(1, 15))

        # 决策理由
        reason = final_decision.get('reason', final_decision.get('rationale', ''))
        if reason:
            story.append(Paragraph("决策理由:", self.styles['heading3']))
            reason_text = str(reason).replace('\n', '<br/>')
            story.append(Paragraph(reason_text, self.styles['normal']))

        # 风险提示
        risk_warning = final_decision.get('risk_warning', final_decision.get('risks', ''))
        if risk_warning:
            story.append(Spacer(1, 10))
            story.append(Paragraph("风险提示:", self.styles['heading3']))
            risk_text = str(risk_warning).replace('\n', '<br/>')
            story.append(Paragraph(risk_text, self.styles['normal']))

        story.append(Spacer(1, 20))
        return story

    def _build_disclaimer_section(self) -> List:
        """构建免责声明部分"""
        story = []

        story.append(Paragraph("免责声明", self.styles['heading1']))

        disclaimer_text = """
        本报告由智投顾问团AI系统自动生成，仅供参考，不构成任何投资建议。
        投资有风险，入市需谨慎。请在做出投资决策前咨询专业的投资顾问。
        本系统及其开发者不对任何投资损失承担责任。

        报告中的数据来源于公开市场信息，我们力求准确但不保证其完整性和及时性。
        过往业绩不代表未来表现，市场存在不可预见的风险。
        """

        story.append(Paragraph(disclaimer_text, self.styles['small']))

        # 版权信息
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"© {datetime.now().year} 智投顾问团 InvestMindPro - AI驱动的智能投资分析系统",
            self.styles['small']
        ))

        return story

    def _format_market_cap(self, value) -> str:
        """格式化市值显示"""
        if value == 'N/A' or value is None:
            return 'N/A'
        try:
            value = float(value)
            if value >= 100000000:  # 亿
                return f"{value / 100000000:.2f}亿"
            elif value >= 10000:  # 万
                return f"{value / 10000:.2f}万"
            else:
                return f"{value:.2f}"
        except (ValueError, TypeError):
            return str(value)

    def generate_base64(
        self,
        stock_info: Dict[str, Any],
        analysis_result: Dict[str, Any],
        agents_analysis: Optional[List[Dict[str, Any]]] = None,
        debate_result: Optional[Dict[str, Any]] = None,
        final_decision: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成Base64编码的PDF内容，用于前端下载"""
        pdf_content = self.generate_analysis_report(
            stock_info, analysis_result, agents_analysis, debate_result, final_decision
        )
        return base64.b64encode(pdf_content).decode('utf-8')


# 单例实例
pdf_generator = PDFReportGenerator()
