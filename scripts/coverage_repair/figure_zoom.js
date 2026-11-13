// Keep figure enlargement on the page, including in the self-contained HTML.
// Opening a data URI in a new tab is blocked by some browsers.
document.addEventListener('click', event => {
    const link = event.target.closest?.('.question-figure a');
    if (!link?.querySelector) return;
    const image = link.querySelector('img');
    if (!image) return;
    event.preventDefault();
    const dialog = document.createElement('dialog');
    dialog.setAttribute('aria-label', '図を拡大');
    dialog.style.cssText = 'width:min(900px,94vw);max-width:94vw;max-height:94vh;box-sizing:border-box;padding:16px;border:1px solid #dce1f1;border-radius:16px;overflow:auto';
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'secondary';
    close.textContent = '閉じる';
    close.addEventListener('click', () => dialog.close());
    const enlarged = image.cloneNode(true);
    enlarged.style.cssText = 'display:block;width:100%;height:auto;margin:12px auto';
    const caption = document.createElement('p');
    caption.textContent = image.alt;
    dialog.append(close, enlarged, caption);
    dialog.addEventListener('close', () => { dialog.remove(); link.focus(); }, { once: true });
    document.body.append(dialog);
    dialog.showModal();
});
