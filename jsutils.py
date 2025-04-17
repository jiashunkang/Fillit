from playwright.async_api import Page

### 查找某个元素的最近的label,span,div的文本内容
### 输入：page, xpath
### 输出：{label:{text:null,distance:null},span:{text:null,distance:null},closest:{tag:null,text:null,distance:null}}
async def get_nearest_text_from_label_span_div(page, xpath: str):
    js_code = f'''
        (() => {{
            const xpath = "{xpath}";
            const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            const inputElement = result.singleNodeValue;

            const output = {{
                label: {{ text: null, distance: null }},
                span: {{ text: null, distance: null }},
                div: {{ text: null, distance: null }},
                closest: {{ tag: null, text: null, distance: null }}
            }};

            if (!inputElement) return output;

            const findNearestNonEmptyText = (element, selector) => {{
                let current = element;
                let distance = 0;
                while (current && current !== document.body) {{
                    const target = current.querySelector(selector);
                    if (target) {{
                        let text = (target.textContent || target.innerText || "").trim();
                        if (text) return {{ text, distance }};
                    }}
                    current = current.parentElement;
                    distance++;
                }}
                return null;
            }};

            // span
            let span = inputElement.closest('span') || inputElement.parentElement.querySelector('span');
            if (span) {{
                let text = (span.textContent || span.innerText || "").trim();
                if (text) {{
                    output.span.text = text;
                    output.span.distance = 0;
                }}
            }}
            if (!output.span.text) {{
                const res = findNearestNonEmptyText(inputElement, 'span');
                if (res) output.span = res;
            }}

            // label
            let label = inputElement.closest('label') || inputElement.parentElement.querySelector('label');
            if (label) {{
                let text = (label.textContent || label.innerText || "").trim();
                if (text) {{
                    output.label.text = text;
                    output.label.distance = 0;
                }}
            }}
            if (!output.label.text) {{
                const res = findNearestNonEmptyText(inputElement, 'label');
                if (res) output.label = res;
            }}

            // div
            let div = inputElement.closest('div') || inputElement.parentElement.querySelector('div');
            if (div) {{
                let text = (div.textContent || div.innerText || "").trim();
                if (text) {{
                    output.div.text = text;
                    output.div.distance = 0;
                }}
            }}
            if (!output.div.text) {{
                const res = findNearestNonEmptyText(inputElement, 'div');
                if (res) output.div = res;
            }}

            // 找最近的那个
            const candidates = ['label', 'span', 'div']
                .map(tag => output[tag])
                .filter(e => e.text !== null);

            if (candidates.length > 0) {{
                const closest = candidates.reduce((a, b) => (a.distance <= b.distance ? a : b));
                for (const tag in output) {{
                    if (output[tag].text === closest.text && output[tag].distance === closest.distance) {{
                        output.closest = {{ tag, ...closest }};
                        break;
                    }}
                }}
            }}

            return output;
        }})()
    '''

    return await page.evaluate(js_code)
