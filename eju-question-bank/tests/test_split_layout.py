import json
import sqlite3
from pathlib import Path
from test_browser_learning import browser_app, open_session, open_reading_settings
from playwright.sync_api import expect
from eju_bank.db import Database


def test_split_layout_and_material_association(browser_app):
    page, db, paper, url = browser_app
    # Open session with PHYSICS_JA (has figure in stemAst) and CHEMISTRY_JA (pure text, no figure)
    sid = open_session(page, db, paper, url, ['PHYSICS_JA', 'CHEMISTRY_JA'])

    # By default, layout mode is SPLIT. The control now lives in the ⚙ popover.
    open_reading_settings(page)
    expect(page.locator('#question-layout')).to_have_value('SPLIT')

    # Question 1 (PHYSICS_JA) has figure in stemAst:
    # Should have .layout-split class, left .q-split-media and right .q-split-content
    physics_card = page.locator('.question-card').first
    expect(physics_card).to_have_class(r'question-card layout-split')
    expect(physics_card.locator('.q-split-media img.figure-img')).to_be_visible()
    expect(physics_card.locator('.q-split-media .figure-btn')).to_have_count(2)  # Pin and Zoom buttons
    expect(physics_card.locator('.q-split-content input[type="radio"]')).to_have_count(4)

    # Question 2 (CHEMISTRY_JA) is pure text, no figure and no materials:
    # Must NOT have .layout-split and must NOT have material-box
    chem_card = page.locator('.question-card').nth(1)
    expect(chem_card).not_to_have_class(r'layout-split')
    expect(chem_card.locator('.material-box')).to_have_count(0)

    # Switch layout to STACKED
    open_reading_settings(page)
    page.locator('#question-layout').select_option('STACKED')
    expect(physics_card).not_to_have_class(r'layout-split')

    # Switch back to SPLIT
    open_reading_settings(page)
    page.locator('#question-layout').select_option('SPLIT')
    expect(physics_card).to_have_class(r'question-card layout-split')

    # Test Pin Figure functionality
    expect(page.locator('#floating-figure-dock')).to_be_hidden()
    physics_card.locator('button:has-text("📌 悬浮固定")').first.click()
    expect(page.locator('#floating-figure-dock')).to_be_visible()
    expect(page.locator('#floating-figure-dock .dock-body img')).to_be_visible()

    # Close floating dock
    page.locator('#floating-figure-dock button:has-text("✕")').click()
    expect(page.locator('#floating-figure-dock')).to_be_hidden()

    # Switch to SINGLE mode: only 1 question card visible and no orphan material boxes
    open_reading_settings(page)
    page.locator('#question-view').select_option('SINGLE')
    expect(page.locator('.question-card:visible')).to_have_count(1)
    # The visible physics card still has its figure on the left
    expect(page.locator('.question-card:visible .q-split-media img.figure-img')).to_be_visible()

    # Advance to Question 2 (Chemistry)
    page.keyboard.press('Escape')
    page.locator('#question-next').click()
    expect(page.locator('.question-card:visible')).to_have_count(1)
    expect(page.locator('.question-card:visible')).not_to_have_class(r'layout-split')


def test_split_layout_narrow_screen_no_overflow(browser_app):
    page, db, paper, url = browser_app
    page.set_viewport_size({'width': 360, 'height': 800})
    sid = open_session(page, db, paper, url, ['PHYSICS_JA'])
    # Split layout collapses cleanly on narrow screen (<= 365px scrollWidth)
    expect(page.locator('.question-card').first).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth') <= 365


def test_material_figure_and_split_layout(browser_app):
    page, db, paper, url = browser_app
    # Open session with JAPANESE_JA which has reading and listening materials with figures
    sid = open_session(page, db, paper, url, ['JAPANESE_JA'])

    # Question 3 (Listening) has a material with figure
    listening_card = page.locator('.question-card').nth(2)
    expect(listening_card).to_have_class(r'question-card layout-split')
    expect(listening_card.locator('.q-split-media img.figure-img')).to_be_visible()
    expect(listening_card.locator('.q-split-media .material-title')).to_contain_text('本题材料 / 配图')
    expect(listening_card.locator('.q-split-content')).to_be_visible()
