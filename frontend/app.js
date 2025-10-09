// ========== CONFIG ==========
const API_URL = window.location.origin;  // Aynı sunucu
// const API_URL = 'http://localhost:5000';  // Local test için

// ========== STATE ==========
let currentProduct = null;
let currentBarcodeSearched = '';
let currentTedarikciKaydiId = null;
let selectedCandidateId = null;
let selectedTedarikciKaydiId = null;
let contextBrand = null;
let contextCategory = null;
let allCandidates = [];
let currentUser = null;  // Seçili kullanıcı/ekip

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Konyalı Optik Sayım Sistemi başlatıldı');

    // Kullanıcıyı yükle
    loadSavedUser();

    // Enter tuşları
    document.getElementById('barkodInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchBarcode();
    });

    document.getElementById('manuelInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') manuelSearch();
    });

    // Fotoğraf seçildiğinde önizleme göster
    const photoInput = document.getElementById('photoInput');
    if (photoInput) {
        photoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const preview = document.getElementById('photoPreview');
                    const previewImg = document.getElementById('photoPreviewImg');
                    if (preview && previewImg) {
                        previewImg.src = e.target.result;
                        preview.style.display = 'block';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // İstatistikleri yükle
    loadStats();
    loadBrands();

    // Her 30 saniyede bir stats güncelle
    setInterval(loadStats, 30000);
});

// ========== BARCODE SEARCH ==========
async function searchBarcode() {
    const barkod = document.getElementById('barkodInput').value.trim();

    if (!barkod) {
        alert('Lütfen barkod girin!');
        return;
    }

    currentBarcodeSearched = barkod;
    showLoading();

    try {
        const response = await fetch(`${API_URL}/api/search-barcode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                barkod: barkod,
                context_brand: contextBrand,
                context_category: contextCategory
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.found) {
            currentTedarikciKaydiId = data.tedarikci_kaydi_id;

            if (data.status === 'direkt') {
                showSuccessResult(data.product, data.confidence);
            } else if (data.status === 'belirsiz') {
                showMultipleResults(data.candidates);
            }
        } else {
            showNotFound(barkod);
        }

    } catch (error) {
        hideLoading();
        console.error('❌ Bağlantı hatası:', error);
        alert('Bağlantı hatası: ' + error.message);
    }
}

// ========== MANUEL SEARCH ==========
async function manuelSearch() {
    const term = document.getElementById('manuelInput').value.trim();

    if (!term || term.length < 2) {
        alert('En az 2 karakter girin!');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_URL}/api/search-manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                term: term,
                context_brand: contextBrand,
                context_category: contextCategory
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.found) {
            if (data.count === 1) {
                currentTedarikciKaydiId = null; // Manuel aramada tedarikçi kaydı yok
                showSuccessResult(data.products[0], 90);
            } else {
                // Çoklu sonuç - candidate formatına çevir
                const candidates = data.products.map(p => ({
                    sku_id: p.id,
                    product: p,
                    tedarikci_kaydi_id: null
                }));
                showMultipleResults(candidates);
            }
        } else {
            alert('Sonuç bulunamadı. Farklı bir terim deneyin.');
        }

    } catch (error) {
        hideLoading();
        console.error('❌ Manuel arama hatası:', error);
        alert('Bağlantı hatası: ' + error.message);
    }
}

// ========== DISPLAY RESULTS ==========
function showSuccessResult(product, confidence) {
    hideAllResults();
    currentProduct = product;

    // Store confidence for extended features
    if (typeof currentConfidence !== 'undefined') {
        window.currentConfidence = confidence;
    }

    document.getElementById('resSku').textContent = product.sku || '-';
    document.getElementById('resMarka').textContent = product.marka || '-';
    document.getElementById('resKategori').textContent = getCategoryName(product.kategori);
    document.getElementById('resModel').textContent = `${product.model_kodu || ''} ${product.model_adi || ''}`.trim() || '-';
    document.getElementById('resRenk').textContent = `${product.renk_adi || ''} (${product.renk_kodu || ''})`;
    document.getElementById('resEkartman').textContent = product.ekartman ? product.ekartman + ' mm' : '-';
    document.getElementById('resConfidence').textContent = `${confidence}%`;

    document.getElementById('resultSuccess').style.display = 'block';
}

function showMultipleResults(candidates) {
    hideAllResults();
    allCandidates = candidates;

    const list = document.getElementById('candidateList');
    list.innerHTML = '';

    candidates.forEach((candidate, index) => {
        const product = candidate.product;
        const item = document.createElement('div');
        item.className = 'candidate-item';
        item.dataset.skuId = candidate.sku_id;
        item.dataset.tedarikciKaydiId = candidate.tedarikci_kaydi_id || '';
        item.onclick = () => selectCandidate(item);

        item.innerHTML = `
            <h4>${product.model_adi || 'Model'} - ${product.ekartman || '?'}mm</h4>
            <p><strong>SKU:</strong> ${product.sku}</p>
            <p><strong>Marka:</strong> ${product.marka || '-'}</p>
            <p><strong>Renk:</strong> ${product.renk_adi} (${product.renk_kodu})</p>
        `;

        list.appendChild(item);

        // İlk adayı otomatik seç
        if (index === 0) {
            selectCandidate(item);
        }
    });

    document.getElementById('resultMultiple').style.display = 'block';
}

function showNotFound(barkod) {
    hideAllResults();
    document.getElementById('notFoundBarcode').textContent = barkod;
    document.getElementById('resultNotFound').style.display = 'block';
}

function hideAllResults() {
    document.getElementById('resultSuccess').style.display = 'none';
    document.getElementById('resultMultiple').style.display = 'none';
    document.getElementById('resultNotFound').style.display = 'none';
}

// ========== CANDIDATE SELECTION ==========
function selectCandidate(element) {
    // Tüm seçimleri kaldır
    document.querySelectorAll('.candidate-item').forEach(item => {
        item.classList.remove('selected');
    });

    // Bu item'ı seç
    element.classList.add('selected');
    selectedCandidateId = element.dataset.skuId;
    selectedTedarikciKaydiId = element.dataset.tedarikciKaydiId || null;
}

async function saveSelectedCandidate() {
    if (!selectedCandidateId) {
        alert('Lütfen bir ürün seçin!');
        return;
    }

    // Manuel arama sonucuysa barkod alanını doldur
    if (!currentBarcodeSearched) {
        currentBarcodeSearched = document.getElementById('manuelInput').value.trim() || 'manuel-arama';
    }

    // Use enhanced save if available, fallback to basic
    if (typeof saveCountEnhanced !== 'undefined') {
        await saveCountEnhanced(selectedCandidateId, 'Belirsiz', selectedTedarikciKaydiId);
    } else {
        await saveCount(selectedCandidateId, 'Belirsiz', selectedTedarikciKaydiId);
    }
}

// ========== SAVE COUNT ==========
async function confirmAndSave() {
    if (!currentProduct) return;

    const skuId = currentProduct.id;
    let eslesmeDurumu = 'Direkt';

    // If barcode is empty, it's a manual search confirmation
    if (!currentBarcodeSearched) {
        currentBarcodeSearched = document.getElementById('manuelInput').value.trim() || 'manuel'; // Use search term or 'manuel' as placeholder
        eslesmeDurumu = 'Manuel';
    }

    // Use enhanced save if available, fallback to basic
    if (typeof saveCountEnhanced !== 'undefined') {
        await saveCountEnhanced(skuId, eslesmeDurumu, currentTedarikciKaydiId);
    } else {
        await saveCount(skuId, eslesmeDurumu, currentTedarikciKaydiId);
    }
}

async function saveNotFound() {
    if (!currentBarcodeSearched) return;

    showLoading();

    try {
        const payload = {
            barkod: currentBarcodeSearched,
            eslesme_durumu: 'Bulunamadı'
        };

        // Context bilgileri
        if (contextBrand) {
            payload.context_brand = contextBrand;
        }

        if (contextCategory) {
            payload.context_category = contextCategory;
        }

        // Notlar
        const notlar = document.getElementById('notesInput')?.value.trim();
        if (notlar) {
            payload.notlar = notlar;
        }

        // Ekip/Kullanıcı bilgisi
        if (currentUser) {
            payload.sayim_yapan = currentUser;
        }

        const response = await fetch(`${API_URL}/api/save-count`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            // Fotoğraf varsa upload et
            const photoInput = document.getElementById('photoInput');
            if (photoInput && photoInput.files.length > 0) {
                await uploadPhoto(data.record_id, photoInput.files[0]);
            }

            // Başarı mesajı göster
            showSuccessToast();

            // Stats güncelle
            loadStats();
        } else {
            alert('Kayıt hatası: ' + data.error);
        }

    } catch (error) {
        hideLoading();
        console.error('❌ Kayıt hatası:', error);
        alert('Bağlantı hatası: ' + error.message);
    }
}

async function uploadPhoto(recordId, photoFile) {
    try {
        const formData = new FormData();
        formData.append('photo', photoFile);
        formData.append('record_id', recordId);

        const response = await fetch(`${API_URL}/api/upload-photo`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (!data.success) {
            console.error('Fotoğraf yükleme hatası:', data.error);
        }
    } catch (error) {
        console.error('Fotoğraf yükleme hatası:', error);
    }
}

function removePhoto() {
    const photoInput = document.getElementById('photoInput');
    const photoPreview = document.getElementById('photoPreview');
    if (photoInput) photoInput.value = '';
    if (photoPreview) photoPreview.style.display = 'none';
}

async function saveCount(skuId, eslesme, tedarikciKaydiId) {
    showLoading();

    try {
        const payload = {
            barkod: currentBarcodeSearched,
            eslesme_durumu: eslesme
        };

        // SKU ID (bulunamadı durumunda null)
        if (skuId) {
            payload.sku_id = skuId;
        }

        // Tedarikçi kaydı
        if (tedarikciKaydiId) {
            payload.tedarikci_kaydi_id = tedarikciKaydiId;
        }

        // Context bilgileri
        if (contextBrand) {
            payload.context_brand = contextBrand;
        }

        if (contextCategory) {
            payload.context_category = contextCategory;
        }

        // Manuel arama terimi (varsa)
        const manuelTerm = document.getElementById('manuelInput').value.trim();
        if (manuelTerm) {
            payload.manuel_arama_terimi = manuelTerm;
        }

        // UTS QR Kodu - hem single hem multiple input'tan kontrol et
        let utsQrInput = document.getElementById('utsQrInput');
        if (!utsQrInput || !utsQrInput.value.trim()) {
            // Multiple result ekranındaki input'u kontrol et
            utsQrInput = document.getElementById('utsQrInputMultiple');
        }
        if (utsQrInput && utsQrInput.value.trim()) {
            payload.uts_qr = utsQrInput.value.trim();
        }

        // Ekip/Kullanıcı bilgisi
        if (currentUser) {
            payload.sayim_yapan = currentUser;
        }

        const response = await fetch(`${API_URL}/api/save-count`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            // Son kaydedilen ürünü sakla (tekrar say için)
            if (currentProduct) {
                lastSavedProduct = {
                    product: currentProduct,
                    confidence: window.currentConfidence || 100
                };
            }

            // Başarı mesajı göster
            showSuccessToast();

            // Stats güncelle (form temizleme olmadan)
            loadStats();
        } else {
            alert('Kayıt hatası: ' + data.error);
        }

    } catch (error) {
        hideLoading();
        console.error('❌ Kayıt hatası:', error);
        alert('Bağlantı hatası: ' + error.message);
    }
}

// ========== USER MANAGEMENT ==========
function changeUser() {
    const select = document.getElementById('userSelect');
    currentUser = select.value;

    // LocalStorage'a kaydet
    if (currentUser) {
        localStorage.setItem('selectedUser', currentUser);
    } else {
        localStorage.removeItem('selectedUser');
    }
}

function loadSavedUser() {
    // Sayfa yüklendiğinde kullanıcıyı hatırla
    const savedUser = localStorage.getItem('selectedUser');
    if (savedUser) {
        currentUser = savedUser;
        const select = document.getElementById('userSelect');
        if (select) {
            select.value = savedUser;
        }
    }
}

// ========== RESET & NAVIGATION ==========
let lastSavedProduct = null;  // Son kaydedilen ürünü tutar

function repeatSameProduct() {
    // Son kaydedilen ürünü tekrar göster
    if (lastSavedProduct) {
        hideAllResults();
        showSuccessResult(lastSavedProduct.product, lastSavedProduct.confidence);
        // UTS input'larını temizle
        const utsInput = document.getElementById('utsQrInput');
        if (utsInput) utsInput.value = '';
        const utsInputMultiple = document.getElementById('utsQrInputMultiple');
        if (utsInputMultiple) utsInputMultiple.value = '';
    } else {
        alert('Tekrar sayılacak ürün bilgisi yok!');
    }
}

function resetForm() {
    document.getElementById('barkodInput').value = '';
    document.getElementById('manuelInput').value = '';

    // UTS input'ları temizle (hem single hem multiple)
    const utsInput = document.getElementById('utsQrInput');
    if (utsInput) {
        utsInput.value = '';
    }
    const utsInputMultiple = document.getElementById('utsQrInputMultiple');
    if (utsInputMultiple) {
        utsInputMultiple.value = '';
    }

    hideAllResults();
    currentProduct = null;
    currentBarcodeSearched = '';
    currentTedarikciKaydiId = null;
    selectedCandidateId = null;
    selectedTedarikciKaydiId = null;
    allCandidates = [];
    document.getElementById('barkodInput').focus();
}

function focusManuel() {
    // Sonuç ekranını gizle ve manuel aramaya odaklan
    hideAllResults();
    document.getElementById('manuelInput').focus();
}

async function skipProduct() {
    // Atla (kaydet) - fotoğraf ve not varsa onlarla kaydet
    if (!currentBarcodeSearched) {
        resetForm();
        return;
    }

    const notlar = document.getElementById('notesInput')?.value.trim() || '';
    const photoInput = document.getElementById('photoInput');
    const hasPhoto = photoInput && photoInput.files.length > 0;

    // Eğer not veya fotoğraf varsa kaydet
    if (notlar || hasPhoto) {
        await saveNotFound();
    } else {
        // Hiçbir şey yoksa direkt atla
        resetForm();
    }
}

// ========== CONTEXT MANAGEMENT ==========
function openContextModal() {
    document.getElementById('contextModal').style.display = 'flex';
}

function closeContextModal() {
    document.getElementById('contextModal').style.display = 'none';
}

function applyContext() {
    const brand = document.getElementById('contextBrand').value;
    const category = document.getElementById('contextCategory').value;

    contextBrand = brand || null;
    contextCategory = category || null;

    updateContextDisplay();
    closeContextModal();
}

function clearContext() {
    contextBrand = null;
    contextCategory = null;
    document.getElementById('contextBrand').value = '';
    document.getElementById('contextCategory').value = '';
    updateContextDisplay();
    closeContextModal();
}

function updateContextDisplay() {
    const btn = document.getElementById('contextText');

    if (contextBrand || contextCategory) {
        const brandName = document.getElementById('contextBrand').selectedOptions[0]?.text || '';
        const categoryName = document.getElementById('contextCategory').selectedOptions[0]?.text || '';
        btn.textContent = `🎯 ${brandName} ${categoryName}`.trim();
        document.querySelector('.btn-context').classList.add('active');
    } else {
        btn.textContent = '🎯 Bağlam Seç';
        document.querySelector('.btn-context').classList.remove('active');
    }
}

// ========== LOAD DATA ==========
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/api/stats`);
        const data = await response.json();

        if (data.success) {
            document.getElementById('todayCount').textContent = data.stats.total;
            document.getElementById('statTotal').textContent = data.stats.total;
            document.getElementById('statDirekt').textContent = data.stats.direkt;
            document.getElementById('statOran').textContent = data.stats.direkt_oran + '%';
        }
    } catch (error) {
        console.error('❌ Stats yükleme hatası:', error);
    }
}

async function loadBrands() {
    try {
        const response = await fetch(`${API_URL}/api/brands`);
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('contextBrand');
            data.brands.forEach(brand => {
                const option = document.createElement('option');
                option.value = brand.id;
                option.textContent = brand.ad;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('❌ Marka yükleme hatası:', error);
    }
}

// ========== UI HELPERS ==========
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    hideAllResults();
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function getCategoryName(code) {
    const names = {
        'OF': 'Optik Çerçeve',
        'GN': 'Güneş Gözlüğü',
        'CM': 'Gözlük Camı',
        'LN': 'Lens'
    };
    return names[code] || code || '-';
}

function showSuccessToast() {
    // HTML'deki success toast section'ını göster
    const successSection = document.getElementById('successToast');
    if (successSection) {
        hideAllResults();
        successSection.style.display = 'block';
        return;
    }

    // Fallback: Basit başarı animasyonu
    const toast = document.createElement('div');
    toast.textContent = '✅ Kaydedildi!';
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--primary);
        color: white;
        padding: 15px 30px;
        border-radius: 8px;
        font-weight: bold;
        z-index: 2000;
        animation: slideDown 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 2000);
}

// ========== ERROR HANDLING ==========
window.addEventListener('error', (e) => {
    console.error('❌ Global error:', e);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('❌ Unhandled promise rejection:', e);
});
