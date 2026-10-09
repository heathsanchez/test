#!/usr/bin/env python3
"""Reconnect native retrieval functions to the blind instruction interface.

Only the instruction and starting URL choose a capability. No reference result
or benchmark identity is passed to any execution function. Existing qualified
collectors are reused without changing their bounded semantics.
"""
from __future__ import annotations

import argparse
import asyncio
import calendar
import json
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from playwright.async_api import async_playwright
from webarena_unified_blind_four_site import site_from_start, actual_start
from webarena_unified_blind_74 import run as run_existing

BASES = {'shopping_admin': 'http://localhost:7780/admin',
         'shopping': 'http://localhost:7770', 'reddit': 'http://localhost:9999'}


def clean(value: str) -> str:
    return re.sub(r'\s+', ' ', str(value)).strip()


def parse_request(site: str, intent: str):
    """Return a descriptive capability and instruction-derived parameters."""
    text = clean(intent)
    low = text.casefold()
    if site == 'shopping_admin':
        if re.match(r'Get (?:the total payment amount|the payment difference) ', text, re.I):
            from webarena_shopping_admin_payment_fold_v2 import parse_query
            parse_query(text)
            return 'admin_payment', {'instruction': text}
        if re.match(r'Get the billing name of the (?:oldest|most recent|newest) ', text, re.I):
            from webarena_shopping_admin_visible_order_selector import parse_selector
            return 'admin_visible_order', parse_selector(text)
        if low.startswith('get customer email(s) who '):
            from webarena_shopping_admin_customer_order_counts import parse_criterion
            return 'admin_order_counts', parse_criterion(text)
        m = re.fullmatch(r'Get the top (\d+) search term(?:\(s\)|s) (in my store|that match available products in the store)\.?', text, re.I)
        if m:
            n = int(m[1])
            if not 1 <= n <= 1000:
                raise ValueError('search-term count outside bounded collector scope')
            return 'admin_search_terms', {'n': n, 'available_only': m[2].casefold().startswith('that')}
        if low.startswith('get the product name and final price (low to high) of the '):
            from webarena_shopping_admin_order_detail import parse_task
            return 'admin_order_detail', parse_task(text)
        m = re.fullmatch(r'Return the customer nickname\(s\) who gave a rating of ([1-5]) stars or below for (.+)', text, re.I)
        if m:
            # A product-family query is not equivalent to an exact-product query.
            if m[2].casefold().endswith(' products'):
                return None
            return 'admin_ratings', {'product': m[2], 'limit': int(m[1]), 'fields': 'nickname'}
        m = re.match(r'Get the title and rating for all reviews with ([1-5]) stars or below for (.+?)(?:\. Return |$)', text, re.I)
        if m:
            return 'admin_ratings', {'product': m[2].rstrip('.'), 'limit': int(m[1]), 'fields': 'title_rating'}
        m = re.match(r'Get the customer name and email with phone number ([+\d ()-]+)(?:\.|$)', text, re.I)
        if m:
            return 'admin_customer_lookup', {'phone': m[1].strip()}
        m = re.match(r'Give me the (name and color|material|product names and the sizes) of the products that have (\d+(?:-\d+)?) units left(?:\.|$)', text, re.I)
        if m:
            attributes = {'name and color': ['name', 'color'], 'material': ['material'],
                          'product names and the sizes': ['name', 'size']}
            return 'admin_inventory', {'quantity': m[2], 'attributes': attributes[m[1].casefold()]}
        m = re.fullmatch(r'Get the total number of reviews that our store received so far that mention term "([^"]+)"', text, re.I)
        if m:
            return 'admin_review_count', {'kind': 'term', 'term': m[1]}
        m = re.fullmatch(r'How many reviews did our shop receive in ([A-Za-z]+) (\d{4})\?', text, re.I)
        if m:
            months = {name.casefold(): i for i in range(1, 13)
                      for name in (calendar.month_name[i], calendar.month_abbr[i])}
            if m[1].casefold() not in months:
                raise ValueError('unknown review month')
            return 'admin_review_count', {'kind': 'month', 'month': months[m[1].casefold()], 'year': int(m[2])}
    elif site == 'shopping':
        m = re.fullmatch(r'Get name\(s\) of reviewer\(s\) who mention (.+?) for the product on the current page', text, re.I)
        if m:
            return 'shopping_reviewers', {'description': m[1]}
        m = re.match(r'Return the date I last ordered my (.+?)\. Return the date ', text, re.I)
        if m:
            return 'shopping_last_ordered', {'product': m[1]}
        m = re.match(r'Get the (size|color) of the (.+?) I bought ((?:in \d{4})|(?:[A-Za-z]+ \d{4}))(?:\.|$)', text, re.I)
        if m:
            return 'shopping_order_attributes', {'attribute': m[1].casefold(), 'product': m[2], 'period': m[3]}
        m = re.match(r'Today is ([A-Za-z]+ \d{1,2}, \d{4})\. Get how many complete orders I have over the past year, and the total amount of money I spent \(including shipping and handling fees\)', text, re.I)
        if m:
            return 'shopping_order_summary', {'mode': 'past_year', 'today': datetime.strptime(m[1], '%B %d, %Y').isoformat()}
        m = re.fullmatch(r'Get the total cost of my latest order marked as "([^"]+)"\.?', text, re.I)
        if m:
            return 'shopping_order_summary', {'mode': 'cost', 'status': m[1]}
        m = re.fullmatch(r'Get the order number of my most recent (.+?) order\.?', text, re.I)
        if m:
            return 'shopping_order_summary', {'mode': 'number', 'status': m[1]}
        m = re.match(r'How much refund should I expect from my orders canceled, if any, in ((?:[A-Za-z]+ )?\d{4})(.*)', text, re.I)
        if m:
            return 'shopping_refund', {'period': m[1], 'conditions': m[2]}
        m = re.fullmatch(r'Who gave ([1-5](?: or [1-5])?) stars for (.+?) from (.+)', text, re.I)
        if m:
            return 'shopping_brand_reviewers', {'stars': [int(x) for x in re.findall(r'[1-5]', m[1])], 'category': m[2], 'brand': m[3]}
        m = re.match(r'Return how much I spent on (.+?) shopping during (.+?) without considering shipping and handling fee\.', text, re.I)
        if m:
            return 'shopping_category_spend', {'category': m[1], 'period': m[2]}
    return None


def response(data, *, missing_if_empty=False):
    missing = missing_if_empty and not data
    return {'task_type': 'RETRIEVE', 'status': 'NOT_FOUND_ERROR' if missing else 'SUCCESS',
            'retrieved_data': None if missing else data, 'error_details': None}


async def visit(page, url):
    result = await page.goto(url, wait_until='networkidle', timeout=120000)
    if result is None or result.status != 200:
        raise RuntimeError(f'retrieval document failed: {url}; HTTP {getattr(result,"status",None)}')


async def execute(page, context, site, capability, args, start_url):
    base = BASES[site]
    evidence = {'capability': capability, 'parameters': args}
    if capability == 'admin_visible_order':
        import webarena_shopping_admin_visible_order_selector as f
        await visit(page, base + f.ORDER_GRID)
        await f.rewind_first(page)
        rows = await f.scan(page)
        result, selected = f.make_response(rows, args)
        return result, {**evidence, 'rows_scanned': len(rows), 'selected': selected}
    if capability == 'admin_order_counts':
        import webarena_shopping_admin_customer_order_counts as f
        await visit(page, base + f.ORDER_GRID)
        await f.expose_customer_email(page)
        await f.rewind_first(page)
        rows = await f.scan_all(page)
        return f.answer(rows, args), {**evidence, 'rows_scanned': len(rows)}
    if capability == 'admin_search_terms':
        import webarena_shopping_admin_search_terms as f
        await visit(page, base + f.SEARCH_TERMS)
        rows = await f.scan_all(page)
        return response(f.answer(rows, args)), {**evidence, 'rows_scanned': len(rows)}
    if capability == 'admin_order_detail':
        import webarena_shopping_admin_order_detail as f
        await visit(page, base + f.ORDER_GRID)
        selected = await f.select_order(page, args)
        if not selected:
            return response([], missing_if_empty=True), evidence
        await visit(page, selected['href'])
        data = await f.extract_items(page)
        return response(data), {**evidence, 'selected': selected}
    if capability == 'admin_ratings':
        import webarena_shopping_admin_review_ratings_authority55 as f
        await visit(page, base + f.REVIEWS)
        rows = await f.matching_reviews(page, args['product'])
        detail = await context.new_page()
        selected = []
        for row in rows:
            stars = await f.star_value(detail, row['href'])
            if stars <= args['limit']:
                selected.append({**row, 'stars': stars})
        data = [row['nickname'] for row in selected] if args['fields'] == 'nickname' else [
            {'title': row['title'], 'rating': str(row['stars'])} for row in selected]
        return response(data, missing_if_empty=True), {**evidence, 'selected': selected}
    if capability == 'admin_customer_lookup':
        import webarena_shopping_admin_customer_lookup as f
        await visit(page, base + f.CUSTOMERS)
        rows = await f.scan_all(page)
        found = [{'name': row['name'], 'email': row['email']} for row in rows
                 if f.digits(row['phone']) == f.digits(args['phone'])]
        return response(found), {**evidence, 'rows_scanned': len(rows)}
    if capability == 'admin_review_count':
        import webarena_shopping_admin_review_counts as f
        await visit(page, base + f.REVIEW_GRID)
        value = await f.filtered_term_count(page, args['term']) if args['kind'] == 'term' else await f.filtered_date_count(page, args)
        return response([value]), {**evidence, 'observed_count': value}
    if capability == 'admin_inventory':
        import webarena_shopping_admin_inventory_attributes as f
        import webarena_shopping_admin_inventory_attributes_v2 as corrected
        await visit(page, base + f.PRODUCTS)
        products = await corrected.scan_products(page)
        keep = f.qty_rule(args['quantity'])
        attrs = args['attributes']
        selected = []
        for product in products:
            if not keep(product['qty']):
                continue
            row = {'name': product['name'], 'sku': product['sku']}
            suffix = f.variant_suffixes(product['name'])
            for attr in attrs:
                if attr in ('size', 'color') and suffix.get(attr):
                    row[attr] = suffix[attr]
            unresolved = [attr for attr in attrs if attr not in ('name', 'sku') and not row.get(attr)]
            if unresolved:
                row.update(await corrected.enrich(page, product, unresolved))
            if 'material' in attrs and not row.get('material'):
                parent_name = f.parent_name_for_variant(product['name'])
                parent = next((x for x in products if parent_name and clean(x['name']).casefold() == parent_name.casefold()), None)
                if parent and parent.get('href'):
                    row.update(await corrected.enrich(page, parent, ['material']))
            selected.append(row)
        data = [r['material'] for r in selected if r.get('material')] if attrs == ['material'] else [{k: r.get(k) for k in attrs} for r in selected]
        return response(data, missing_if_empty=True), {**evidence, 'products_scanned': len(products)}
    if capability == 'shopping_reviewers':
        import webarena_shopping_reviewer_mentions as f
        await visit(page, actual_start(start_url))
        await f.activate_reviews(page)
        rows = await f.collect(page)
        rule, limit = f.predicate(args['description'])
        names = list(dict.fromkeys(r['author'] for r in rows if f.matches(r, rule, limit)))
        return response(names, missing_if_empty=True), {**evidence, 'reviews_scanned': len(rows), 'rule': rule}
    if capability == 'shopping_last_ordered':
        import webarena_shopping_last_ordered_date_v2 as f
        aliases = [args['product']] + await f.catalog_aliases(page, base, args['product'])
        orders, pages = await f.collect_history(page, base)
        selected = None
        for order in orders:
            names = await f.item_names(page, order['href'])
            if any(f.product_match(alias, name) for alias in aliases for name in names):
                selected = {**order, 'names': names}
                break
        return response([selected['date_text'] if selected else None]), {**evidence, 'pages': pages, 'selected': selected}
    if capability == 'shopping_order_attributes':
        import webarena_shopping_order_history_probe as f
        bounds = f.parse_period(args['period'])
        aliases = [args['product']] + await f.catalog_aliases(page, base, args['product'])
        rows = await f.history(page, base)
        selected = []
        for order in rows:
            if f.in_period(order['date'], bounds):
                for item in await f.order_items(page, order['href']):
                    if any(f.product_match(alias, item['name']) for alias in aliases):
                        selected.append(item)
        return response(f.response_data(args['attribute'], selected), missing_if_empty=True), {**evidence, 'selected': selected}
    if capability == 'shopping_order_summary':
        import webarena_shopping_order_summary as f
        rows = await f.orders(page, base)
        if args['mode'] == 'past_year':
            today = datetime.fromisoformat(args['today'])
            # Calendar-year interval; leap-day anniversaries use February 28.
            begin = today.replace(year=today.year-1, day=min(today.day, calendar.monthrange(today.year-1, today.month)[1]))
            end = today.replace(hour=23, minute=59, second=59)
            chosen = [row for row in rows if begin <= row['date'] <= end and f.status_norm(row['status']) == 'complete']
            amount = sum((row['total'] for row in chosen), Decimal('0')).quantize(Decimal('.01'))
            data = [{'order_count': len(chosen), 'amount': float(amount)}]
        else:
            chosen = [row for row in rows if f.status_norm(row['status']) == f.status_norm(args['status'])]
            data = [] if not chosen else [float(chosen[0]['total']) if args['mode'] == 'cost' else chosen[0]['order_no']]
        return response(data, missing_if_empty=True), {**evidence, 'selected': chosen}
    if capability == 'shopping_refund':
        import webarena_shopping_refunds as f
        bounds = f.period(args['period'])
        rows = await f.collect_orders(page, base)
        chosen = [r for r in rows if f.within(r['date'], bounds) and r['status'].casefold() in ('canceled','cancelled')]
        value = sum((r['total'] for r in chosen), Decimal('0'))
        kept_found = False
        adjustments = []
        for row in chosen:
            amount, detail, kept_found = await f.adjustment(page, row, args['conditions'], kept_found)
            value -= amount
            adjustments.append(detail)
        if re.search(r'only kept the\s+(.+?)\s+and the shop', args['conditions'], re.I) and not kept_found:
            raise RuntimeError('retained item absent from observed cancelled orders')
        return response([float(value.quantize(Decimal('.01')))]), {**evidence, 'adjustments': adjustments, 'orders': len(chosen)}
    if capability == 'shopping_brand_reviewers':
        import webarena_shopping_brand_reviewers as f
        products, observed = await f.search_products(page, base, args['category'], args['brand'])
        rows = []
        for product in products:
            rows.extend(await f.collect_reviews(page, product['href']))
        names = list(dict.fromkeys(r['author'] for r in rows if int(round(r['stars'])) in args['stars']))
        return response(names, missing_if_empty=True), {**evidence, 'products': products, 'reviews_scanned': len(rows)}
    if capability == 'shopping_category_spend':
        import webarena_shopping_category_spend as f
        import webarena_shopping_category_spend_v2 as corrected
        period = f.parse_time(args['period'])
        await visit(page, base)
        rows = await f.order_rows(page, base)
        value = Decimal('0')
        selected = []
        for row in rows:
            if not f.in_time(row['date'], period):
                continue
            for item in await f.items(page, row):
                product = await corrected.product_categories(page, base, item['name'])
                included = corrected.category_match(args['category'], product.get('categories') or [])
                selected.append({'name': item['name'], 'subtotal': item['subtotal'], 'included': included})
                if included:
                    value += item['subtotal']
        return response([float(value.quantize(Decimal('.01')))]), {**evidence, 'items': selected}
    raise ValueError(f'unknown retrieval capability: {capability}')


async def run(intent: str, start_url: str, out: Path):
    site = site_from_start(start_url)
    parsed = parse_request(site, intent)
    if parsed is None:
        return await run_existing(intent, start_url, out)
    capability, args = parsed
    out.mkdir(parents=True, exist_ok=True)
    if capability == 'admin_payment':
        from webarena_shopping_admin_payment_fold_v2 import solve
        value, evidence = await solve(BASES[site], intent)
        result = response([float(value)])
    else:
        from webarena_shopping_order_history_probe import AUTH_HEADER as shopping_auth
        from webarena_reddit_submit_v3 import AUTH as reddit_auth
        from webarena_unified_blind_four_site import ADMIN_AUTH
        headers = {'shopping': shopping_auth, 'reddit': reddit_auth, 'shopping_admin': ADMIN_AUTH}[site]
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(extra_http_headers=headers)
            try:
                page = await context.new_page()
                result, evidence = await execute(page, context, site, capability, args, start_url)
            finally:
                await context.close()
                await browser.close()
    (out / 'agent_response.json').write_text(json.dumps(result, indent=2) + '\n')
    (out / 'capability_evidence.json').write_text(json.dumps(
        {'site': site, 'intent': intent, 'start_url': start_url, 'capability': capability, 'evidence': evidence},
        indent=2, default=str, ensure_ascii=False) + '\n')
    print(json.dumps({'site': site, 'capability': capability, 'status': result['status']}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--intent', required=True)
    parser.add_argument('--start-url', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    asyncio.run(run(args.intent, args.start_url, Path(args.output_dir)))


if __name__ == '__main__':
    main()
