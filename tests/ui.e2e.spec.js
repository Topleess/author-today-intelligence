const { test, expect } = require('@playwright/test');
const url = 'http://127.0.0.1:8791/?e2e=1#overview';
for (const viewport of [{name:'desktop',width:1280,height:800},{name:'mobile',width:390,height:844}]) {
  test(`${viewport.name} decision-first flow`, async ({page}) => {
    const errors=[];
    page.on('console',m=>{ if(m.type()==='error') errors.push(m.text()) });
    await page.setViewportSize(viewport);
    await page.goto(url);
    await expect(page.getByText('Есть изменения у 18 книг.')).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(viewport.width);

    await page.getByRole('button',{name:'Открыть книгу'}).first().click();
    await expect(page.getByRole('heading',{name:'Казачонок 1862. Том 10'})).toBeVisible();
    await expect(page.getByText('119 527 − 119 439 = +88')).toBeVisible();
    await page.getByText('Показать исходные точки').click();
    await page.getByText('Технические сведения').first().click();
    await expect(page.getByRole('link',{name:'Открыть исходный адрес'}).first()).toHaveAttribute('href',/^https:\/\/author\.today\//);

    await page.locator('[data-go-section="rankings"]:visible').first().click();
    await expect(page.getByText(/место в top-25/).first()).toBeVisible();
    await page.locator('[data-go-section="readers"]:visible').first().click();
    await expect(page.getByText('Два комментария — это ещё не мнение всех читателей.')).toBeVisible();
    await page.getByText('Открыть комментарий и источник').first().click();
    await expect(page.getByRole('link',{name:'Открыть оригинал'}).first()).toHaveAttribute('href',/^https:\/\/author\.today\//);
    expect(errors).toEqual([]);
  });
}
