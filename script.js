// Agregador de Pesquisas Eleitorais 2026

function applyDarkModeCandidateColors() {
  const isDarkMode = document.body.classList.contains('dark-mode');
  const samaraColor = isDarkMode ? '#ffffff' : '#212121';

  if (window.graficoInstance) {
    window.graficoInstance.data.datasets.forEach(dataset => {
      const label = dataset.label ? dataset.label.replace(' (pesquisas)', '') : '';
      if (label === 'Samara') {
        dataset.borderColor = samaraColor;
        dataset.backgroundColor = dataset.label.endsWith(' (pesquisas)')
          ? samaraColor
          : 'transparent';
      }
    });
    window.graficoInstance.update();
  }

  const mediaItems = document.querySelectorAll('#media-final-items .media-item');
  mediaItems.forEach(item => {
    const itemName = item.querySelector('.media-item-name');
    if (itemName && itemName.textContent.startsWith('Samara')) {
      const bullet = item.querySelector('span');
      if (bullet) bullet.style.color = samaraColor;
    }
  });
}

// Dark Mode Toggle
document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('toggle-dark');
  const body = document.body;
  
  // Verificar preferência salva
  const isDarkMode = localStorage.getItem('darkMode') === 'true';
  if (isDarkMode) {
    body.classList.add('dark-mode');
    toggleBtn.textContent = '☀️';
  }
  applyDarkModeCandidateColors();
  
  // Toggle ao clicar
  toggleBtn.addEventListener('click', function() {
    body.classList.toggle('dark-mode');
    const isNow = body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isNow);
    toggleBtn.textContent = isNow ? '☀️' : '🌙';
    applyDarkModeCandidateColors();
  });
  
  // Changelog Modal
  const changelogBtn = document.getElementById('btn-version');
  const changelogModal = document.getElementById('changelog-modal');
  const modalClose = document.querySelector('.modal-close');
  
  changelogBtn.addEventListener('click', async function() {
    try {
      const response = await fetch('./data/changelog.json');
      const changelog = await response.json();
      
      const changelogBody = document.getElementById('changelog-body');
      changelogBody.innerHTML = '';
      
      changelog.versoes.forEach(versao => {
        const versionDiv = document.createElement('div');
        versionDiv.className = 'changelog-version';
        
        let notasHtml = '';
        versao.notas.forEach(nota => {
          notasHtml += `<li>${nota}</li>`;
        });
        
        versionDiv.innerHTML = `
          <h3>v${versao.versao}</h3>
          <div class="changelog-date">${new Date(versao.data).toLocaleDateString('pt-BR')}</div>
          <ul class="changelog-notes">
            ${notasHtml}
          </ul>
        `;
        changelogBody.appendChild(versionDiv);
      });
      
      changelogModal.classList.add('show');
    } catch (error) {
      console.error('Erro ao carregar changelog:', error);
    }
  });
  
  modalClose.addEventListener('click', function() {
    changelogModal.classList.remove('show');
  });
  
  changelogModal.addEventListener('click', function(e) {
    if (e.target === changelogModal) {
      changelogModal.classList.remove('show');
    }
  });

  const btnTurno1 = document.querySelectorAll('#btn-turno-1');
  const btnTurno2 = document.querySelectorAll('#btn-turno-2');
  const secPrimeiro = document.getElementById('grafico');
  const secSegundo = document.getElementById('grafico-segundo');

  function ativarTurno(turno) {
    if (turno === 1) {
      btnTurno1.forEach(btn => btn.classList.add('ativo'));
      btnTurno2.forEach(btn => btn.classList.remove('ativo'));
      secPrimeiro.classList.remove('hidden');
      secSegundo.classList.add('hidden');
    } else {
      btnTurno1.forEach(btn => btn.classList.remove('ativo'));
      btnTurno2.forEach(btn => btn.classList.add('ativo'));
      secPrimeiro.classList.add('hidden');
      secSegundo.classList.remove('hidden');
    }
  }

  btnTurno1.forEach(btn => btn.addEventListener('click', () => ativarTurno(1)));
  btnTurno2.forEach(btn => btn.addEventListener('click', () => ativarTurno(2)));

  // Toggle para mostrar/ocultar pontos
  const togglePontos = document.getElementById('toggle-pontos');
  const togglePontosSegundo = document.getElementById('toggle-pontos-segundo');
  
  if (togglePontos) {
    togglePontos.addEventListener('change', () => {
      const spanText = togglePontos.parentElement.querySelector('span');
      spanText.textContent = togglePontos.checked ? 'Não Mostrar Pesquisas' : 'Mostrar Pesquisas';
      
      if (window.graficoInstance) {
        window.graficoInstance.data.datasets.forEach(dataset => {
          if (dataset.label.includes('(pesquisas)')) {
            dataset.hidden = !togglePontos.checked;
          }
        });
        window.graficoInstance.update();
      }
    });
  }
  
  if (togglePontosSegundo) {
    togglePontosSegundo.addEventListener('change', () => {
      const spanText = togglePontosSegundo.parentElement.querySelector('span');
      spanText.textContent = togglePontosSegundo.checked ? 'Não Mostrar Pesquisas' : 'Mostrar Pesquisas';
      
      if (window.graficoSegundoInstance) {
        window.graficoSegundoInstance.data.datasets.forEach(dataset => {
          if (dataset.label.includes('(pesquisas)')) {
            dataset.hidden = !togglePontosSegundo.checked;
          }
        });
        window.graficoSegundoInstance.update();
      }
    });
  }

  // Initialize button text based on checkbox state
  if (togglePontos) {
    const spanPrimeiroTurno = togglePontos.parentElement.querySelector('span');
    spanPrimeiroTurno.textContent = togglePontos.checked ? 'Não Mostrar Pesquisas' : 'Mostrar Pesquisas';
  }
  
  if (togglePontosSegundo) {
    const spanSegundoTurno = togglePontosSegundo.parentElement.querySelector('span');
    spanSegundoTurno.textContent = togglePontosSegundo.checked ? 'Não Mostrar Pesquisas' : 'Mostrar Pesquisas';
  }

  ativarTurno(1);
});

async function montarGrafico() {
  console.log('Iniciando montarGrafico...');
  try {
    const cacheBuster = `?t=${Date.now()}`;
    const resposta = await fetch(`./data/primeiro_turno/pesquisas_2026_normalizado.json${cacheBuster}`);
    const pesquisas = await resposta.json();
    console.log('✓ Pesquisas carregadas:', pesquisas.length);
    
    // Carregar médias móveis pré-calculadas
    const respostaMM = await fetch(`./data/primeiro_turno/media_movel_precalculada.json${cacheBuster}`);
    const mediaMovelData = await respostaMM.json();
    console.log('✓ Médias móveis carregadas:', Object.keys(mediaMovelData.candidatos));
  
  const ctx = document.getElementById('graficoVotos').getContext('2d');
  
  // Use moving average data order (already sorted by date)
  // Create registro objects from MM data to maintain alignment
  const registros = mediaMovelData.datas.map((d, i) => ({
    data: new Date(d).toLocaleDateString('pt-BR', { year: 'numeric', month: 'short', day: 'numeric' }),
    instituto: mediaMovelData.institutos[i],
    candidatos: {}
  }));
  
  // Also keep reference to original pesquisas for poll data
  const pesquisasMap = {};
  pesquisas.forEach(p => {
    const key = `${p.instituto}|${p.data}`;
    pesquisasMap[key] = p;
  });
  
  // Fill in candidatos from MM data
  for (const candidato in mediaMovelData.candidatos) {
    registros.forEach((r, i) => {
      r.candidatos[candidato] = mediaMovelData.candidatos[candidato].pesquisas_brutos[i];
    });
  }

  function parseDate(str) {
    if (!str) return null;
    // Handle en-dash, em-dash, and regular hyphen
    str = str.replace(/[–—-]/g, '-');
    let m = str.match(/(\d{1,2})-(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
    if (m) return new Date(`${m[3]} ${m[2]}, ${m[4]}`);
    m = str.match(/(\d{1,2})\s+([A-Za-z]+)\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
    if (m) return new Date(`${m[4]} ${m[3]}, ${m[5]}`);
    m = str.match(/(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
    if (m) return new Date(`${m[2]} ${m[1]}, ${m[3]}`);
    return null;
  }

  const datas = mediaMovelData.datas.map(d => new Date(d));
  
  const registrosFiltrados = registros;
  const datasFiltradas = datas;
  const series = {
    Lula: registrosFiltrados.map(r => r.candidatos?.Lula ?? null),
    Flávio: registrosFiltrados.map(r => r.candidatos?.Flávio ?? null),
    Caiado: registrosFiltrados.map(r => r.candidatos?.Caiado ?? null),
    Zema: registrosFiltrados.map(r => r.candidatos?.Zema ?? null),
    Renan: registrosFiltrados.map(r => r.candidatos?.Renan ?? null),
    Cury: registrosFiltrados.map(r => r.candidatos?.Cury ?? null),
    Samara: registrosFiltrados.map(r => r.candidatos?.Samara ?? null)
  };

  function movingAverageByDate(values, dates, windowDays = 31) {
    const out = [];
    const msWindow = windowDays * 24 * 60 * 60 * 1000;
    
    // First pass: calculate moving averages ONLY for this candidate's data
    for (let i = 0; i < values.length; i++) {
      const base = dates[i];
      if (!base || values[i] == null) { 
        out.push(null); 
        continue; 
      }
      let sum = 0, cnt = 0;
      for (let j = 0; j < values.length; j++) {
        if (values[j] == null) continue; // Skip if no data for this candidate
        const d = dates[j];
        if (!d) continue;
        if (Math.abs(d - base) <= msWindow) { 
          sum += values[j]; 
          cnt++; 
        }
      }
      out.push(cnt ? sum / cnt : null);
    }
    
    // Second pass: interpolate nulls linearly
    for (let i = 0; i < out.length; i++) {
      if (out[i] === null) {
        let prevIdx = -1, nextIdx = -1;
        
        // Find previous non-null value
        for (let j = i - 1; j >= 0; j--) {
          if (out[j] !== null) { prevIdx = j; break; }
        }
        
        // Find next non-null value
        for (let j = i + 1; j < out.length; j++) {
          if (out[j] !== null) { nextIdx = j; break; }
        }
        
        // Linear interpolation
        if (prevIdx !== -1 && nextIdx !== -1) {
          const ratio = (i - prevIdx) / (nextIdx - prevIdx);
          out[i] = out[prevIdx] + (out[nextIdx] - out[prevIdx]) * ratio;
        } else if (prevIdx !== -1) {
          out[i] = out[prevIdx];
        } else if (nextIdx !== -1) {
          out[i] = out[nextIdx];
        }
      }
    }
    
    return out;
  }

  const labels = registrosFiltrados.map((_, i) => i + 1);
  const datasets = [];
  const colors = {
    Lula: '#e53935',
    Flávio: '#43a047',
    Caiado: '#1565c0',
    Zema: '#ff9800',
    Renan: '#FDD835',
    Cury: '#81c784',
    Samara: document.body.classList.contains('dark-mode') ? '#ffffff' : '#212121'
  };
  
  // Mapa de nomes: chave do series -> chave do JSON pré-calculado
  const candidatoMap = {
    Lula: 'Lula',
    Flávio: 'Flávio',
    Caiado: 'Caiado',
    Zema: 'Zema',
    Renan: 'Renan',
    Cury: 'Cury',
    Samara: 'Samara'
  };

  // Mapa de índice para data para cálculo de posição relativa
  const todasAsDatas = mediaMovelData.datas.map(d => new Date(d).getTime());
  const minDateMs = Math.min(...todasAsDatas);
  const maxDateMs = Math.max(...todasAsDatas);
  const totalMs = maxDateMs - minDateMs;

  for (const displayName of Object.keys(series)) {
    // Converter nome para a chave correta no JSON pré-calculado
    const jsonKey = candidatoMap[displayName];
    const mmData = mediaMovelData.candidatos[jsonKey];
    if (!mmData) continue;
    
    // Smooth line dataset - usa média móvel pré-calculada
    const lineData = mmData.media_movel.map((avg, i) => {
      if (avg === null) return null;
      return {
        x: i / (registros.length - 1) * (registros.length - 1),
        y: avg,
        instituto: 'Média móvel',
        data: registros[i].data
      };
    }).filter(d => d !== null);
    
    datasets.push({
      label: displayName,
      data: lineData,
      borderColor: colors[displayName] || '#666',
      backgroundColor: 'transparent',
      tension: 0.4,
      fill: false,
      pointRadius: 0,
      pointHoverRadius: 5,
      borderWidth: 2,
      parsing: {
        xAxisKey: 'x',
        yAxisKey: 'y'
      }
    });
    
    // Raw points dataset - posicionados pela data real
    const pointsData = [];
    for (let i = 0; i < mmData.pesquisas_brutos.length; i++) {
      const val = mmData.pesquisas_brutos[i];
      if (val !== null) {
        // Posição relativa baseada na data
        const posicaoRelativa = (todasAsDatas[i] - minDateMs) / totalMs * (registros.length - 1);
        pointsData.push({
          x: posicaoRelativa,
          y: val,
          instituto: registrosFiltrados[i].instituto,
          data: registrosFiltrados[i].data
        });
      }
    }
    
    datasets.push({
      label: `${displayName} (pesquisas)`,
      data: pointsData,
      borderColor: colors[displayName] || '#666',
      backgroundColor: colors[displayName] || '#666',
      showLine: false,
      pointRadius: 4,
      pointHoverRadius: 6,
      parsing: {
        xAxisKey: 'x',
        yAxisKey: 'y'
      }
    });
  }

  const chart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      clip: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            filter: (item) => !item.text.includes('(pesquisas)'),
            usePointStyle: true,
            padding: 15,
            font: { size: 12 }
          },
          onClick: (e, item, legend) => {
            const candidateName = item.text;
            // Toggle visibility for both line and points
            const chart = legend.chart;
            const togglePontos = document.getElementById('toggle-pontos');
            
            chart.data.datasets.forEach((dataset) => {
              if (dataset.label === candidateName) {
                // Toggle the main line
                dataset.hidden = !dataset.hidden;
              } else if (dataset.label === `${candidateName} (pesquisas)`) {
                // For pesquisas: if main line is becoming hidden, hide pesquisas too
                // Otherwise, respect the toggle state
                const mainLineHidden = chart.data.datasets.find(d => d.label === candidateName).hidden;
                dataset.hidden = mainLineHidden || !togglePontos.checked;
              }
            });
            chart.update();
          }
        },
        title: { display: false },
        tooltip: {
          mode: 'nearest',
          intersect: false,
          callbacks: {
            title: function(context) {
              if (!context || context.length === 0) return '';
              const raw = context[0].raw;
              if (raw && raw.instituto && raw.data) {
                // Traduz mês abreviado (inglês e português) para português completo
                const mesesTraducao = {
                  'Jan': 'Janeiro', 'January': 'Janeiro',
                  'Feb': 'Fevereiro', 'February': 'Fevereiro',
                  'Mar': 'Março', 'March': 'Março',
                  'Apr': 'Abril', 'April': 'Abril',
                  'May': 'Maio',
                  'Jun': 'Junho', 'June': 'Junho',
                  'Jul': 'Julho', 'July': 'Julho',
                  'Aug': 'Agosto', 'August': 'Agosto',
                  'Sep': 'Setembro', 'September': 'Setembro', 
                  'Oct': 'Outubro', 'October': 'Outubro', 
                  'Nov': 'Novembro', 'November': 'Novembro',
                  'Dec': 'Dezembro', 'December': 'Dezembro'
                };
                
                let dataFormatada = raw.data;
                // Substitui mês abreviado ou em inglês por completo em português
                for (const [abrev, completo] of Object.entries(mesesTraducao)) {
                  const regex = new RegExp(abrev, 'gi');
                  dataFormatada = dataFormatada.replace(regex, completo);
                }
                
                return `${raw.instituto} - ${dataFormatada}`;
              }
              return '';
            },
            label: function(context) {
              let label = context.dataset.label || '';
              label = label.replace(' (pesquisas)', '');
              const value = context.parsed.y;
              
              if (value !== null) {
                return `${label}: ${value.toFixed(1)}%`;
              }
              return label;
            }
          }
        }
      },
      scales: {
        x: { 
          display: false,
          type: 'linear',
          max: registros.length - 1,
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          min: 0,
          max: 60,
          title: { display: true, text: 'Votos (%)' },
          grid: {
            display: false
          }
        }
      }
    }
  });

  // Armazenar instância do gráfico para controlar pontos
  window.graficoInstance = chart;

  // Event listener removed - filtering is now done via legend click

  // Timeline filtering with dual range
  const timelineStart = document.getElementById('timeline-start');
  const timelineEnd = document.getElementById('timeline-end');
  const timelineLabel = document.getElementById('timeline-label');
  const timelineTrack = document.getElementById('timeline-track');
  
  // Get date range - filter out nulls
  const validDates = datasFiltradas.filter(d => d !== null && d !== undefined);
  
  if (validDates.length === 0) {
    console.error('No valid dates found');
    return;
  }
  
  const minDate = new Date(Math.min(...validDates.map(d => d.getTime())));
  const maxDate = new Date(Math.max(...validDates.map(d => d.getTime())));
  
  function formatDate(date) {
    const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
  }
  
  function updateTimeline() {
    const startPercentage = parseInt(timelineStart.value);
    const endPercentage = parseInt(timelineEnd.value);
    
    // Ensure start is not greater than end
    if (startPercentage > endPercentage) {
      if (event.target === timelineStart) {
        timelineEnd.value = startPercentage;
      } else {
        timelineStart.value = endPercentage;
      }
    }
    
    const actualStart = Math.min(startPercentage, endPercentage);
    const actualEnd = Math.max(startPercentage, endPercentage);
    
    // Update track background
    timelineTrack.style.background = `linear-gradient(to right, #ddd ${actualStart}%, #1565c0 ${actualStart}%, #1565c0 ${actualEnd}%, #ddd ${actualEnd}%)`;
    
    // Calculate dates
    const timeRange = maxDate - minDate;
    const startTime = minDate.getTime() + (timeRange * actualStart / 100);
    const endTime = minDate.getTime() + (timeRange * actualEnd / 100);
    const startDate = new Date(startTime);
    const endDate = new Date(endTime);
    
    // Filter data points by timeline
    const filteredDataIndices = datasFiltradas.map((d, i) => d >= startDate && d <= endDate ? i : -1).filter(i => i !== -1);
    
    // Update datasets with filtered data
    for (let datasetIdx = 0; datasetIdx < chart.data.datasets.length; datasetIdx++) {
      const dataset = chart.data.datasets[datasetIdx];
      const isSmoothLine = !dataset.label.includes('(pesquisas)');
      const displayName = isSmoothLine ? dataset.label : dataset.label.replace(' (pesquisas)', '');
      const jsonKey = candidatoMap[displayName];
      
      if (isSmoothLine) {
        // Smooth line: filtrar dados pré-calculados
        const mmData = mediaMovelData.candidatos[jsonKey];
        if (!mmData) continue;
        
        const filteredLine = filteredDataIndices
          .map((origIdx, idx) => {
            const avg = mmData.media_movel[origIdx];
            if (avg === null) return null;
            return {
              x: idx / (filteredDataIndices.length - 1 || 1) * (filteredDataIndices.length - 1),
              y: avg,
              instituto: 'Média móvel',
              data: registrosFiltrados[origIdx].data
            };
          })
          .filter(d => d !== null);
        
        dataset.data = filteredLine;
      } else {
        // Raw points: filtrar e reposicionar
        const mmData = mediaMovelData.candidatos[jsonKey];
        if (!mmData) continue;
        
        const filteredPoints = [];
        for (let i = 0; i < filteredDataIndices.length; i++) {
          const origIdx = filteredDataIndices[i];
          const val = mmData.pesquisas_brutos[origIdx];
          if (val !== null) {
            // Posição relativa dentro do período filtrado
            const posicaoRelativa = (filteredDataIndices.length > 1)
              ? i / (filteredDataIndices.length - 1) * (filteredDataIndices.length - 1)
              : 0;
            filteredPoints.push({
              x: posicaoRelativa,
              y: val,
              instituto: registrosFiltrados[origIdx].instituto,
              data: registrosFiltrados[origIdx].data
            });
          }
        }
        
        dataset.data = filteredPoints;
      }
    }
    
    // Update timeline label
    timelineLabel.textContent = `${formatDate(startDate)} a ${formatDate(endDate)}`;
    
    // Update X-axis scale to fill the chart width
    const numFilteredPoints = filteredDataIndices.length;
    chart.options.scales.x.max = numFilteredPoints > 0 ? numFilteredPoints - 1 : 10;
    
    chart.resize();
    chart.update();
    
    // Update média final box
    updateMediaFinalBox(filteredDataIndices);
  }
  
  function updateMediaFinalBox(filteredIndices) {
    const mediaFinalItems = document.getElementById('media-final-items');
    mediaFinalItems.innerHTML = '';
    
    // Updated candidate list for 2026 first round
    const candidatos = ['Lula', 'Flávio', 'Caiado', 'Zema', 'Renan', 'Cury', 'Samara'];
    const samaraCor = document.body.classList.contains('dark-mode') ? '#ffffff' : '#212121';
    const cores = ['#e53935', '#43a047', '#1565c0', '#ff9800', '#FDD835', '#81c784', samaraCor];
    const partidos = ['PT', 'PL', 'PSD', 'NOVO', 'MISSÃO', 'AVANTE', 'UP'];
    
    // Usa sempre o último índice do período geral (não do filtrado), baseado no comprimento dos dados pré-calculados
    const lastIdx = mediaMovelData.datas.length - 1;
    
    // Coleta dados de todos os candidatos
    const dados = [];
    candidatos.forEach((cand, idx) => {
      const mmData = mediaMovelData.candidatos[cand];
      
      if (mmData) {
        const lastValue = mmData.media_movel[lastIdx];
        
        if (lastValue !== null) {
          dados.push({
            nome: cand,
            partido: partidos[idx],
            valor: lastValue,
            cor: cores[idx]
          });
        }
      }
    });
    
    // Ordena por valor (decrescente)
    dados.sort((a, b) => b.valor - a.valor);
    
    // Insere os itens ordenados
    dados.forEach((d) => {
      const item = document.createElement('div');
      item.className = 'media-item';
      item.innerHTML = `
        <span style="color: ${d.cor}; font-size: 1.2rem;">●</span>
        <span class="media-item-name">${d.nome} (${d.partido})</span>
        <span class="media-item-valor">${d.valor.toFixed(1)}%</span>
      `;
      mediaFinalItems.appendChild(item);
    });
  }
  
  timelineStart.addEventListener('input', updateTimeline);
  timelineEnd.addEventListener('input', updateTimeline);
  
  // Initialize timeline with first render
  updateTimeline();
  
  // Force chart resize on window resize
  window.addEventListener('resize', () => {
    chart.resize();
  });
  
  // Initialize timeline label and média final box
  timelineLabel.textContent = `${formatDate(minDate)} a ${formatDate(maxDate)}`;
  updateMediaFinalBox(registros.map((_, i) => i));
  } catch (error) {
    console.error('❌ Erro ao montar gráfico:', error);
    document.getElementById('graficoVotos').innerHTML = `<p style="color: red; padding: 20px;">Erro: ${error.message}</p>`;
  }
}

window.addEventListener('load', () => {
  montarGrafico();
  montarGraficoSegundoTurno();
});

async function montarGraficoSegundoTurno() {
  console.log('Iniciando montarGraficoSegundoTurno...');
  try {
    const cacheBuster = `?t=${Date.now()}`;
    const resposta = await fetch(`./data/segundo_turno/pesquisas_segundo_turno_normalizado.json${cacheBuster}`);
    const pesquisas = await resposta.json();
    console.log('✓ Pesquisas 2º turno carregadas:', pesquisas.length);

    const respostaMM = await fetch(`./data/segundo_turno/media_movel_segundo_turno_precalculada.json${cacheBuster}`);
    const mediaMovelData = await respostaMM.json();
    console.log('✓ Médias móveis 2º turno carregadas:', Object.keys(mediaMovelData.candidatos));

    const ctx = document.getElementById('graficoVotosSegundo').getContext('2d');
    
    // Use moving average data order (already sorted by date)
    const registros = mediaMovelData.datas.map((d, i) => ({
      data: new Date(d).toLocaleDateString('pt-BR', { year: 'numeric', month: 'short', day: 'numeric' }),
      instituto: mediaMovelData.institutos[i],
      candidatos: {}
    }));
    
    // Fill in candidatos from MM data
    for (const candidato in mediaMovelData.candidatos) {
      registros.forEach((r, i) => {
        r.candidatos[candidato] = mediaMovelData.candidatos[candidato].pesquisas_brutos[i];
      });
    }

    function parseDate(str) {
      if (!str) return null;
      // Handle en-dash, em-dash, and regular hyphen
      str = str.replace(/[–—-]/g, '-');
      let m = str.match(/(\d{1,2})-(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
      if (m) return new Date(`${m[3]} ${m[2]}, ${m[4]}`);
      m = str.match(/(\d{1,2})\s+([A-Za-z]+)\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
      if (m) return new Date(`${m[4]} ${m[3]}, ${m[5]}`);
      m = str.match(/(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
      if (m) return new Date(`${m[2]} ${m[1]}, ${m[3]}`);
      return null;
    }

    const datas = mediaMovelData.datas.map(d => new Date(d));
    const registrosFiltrados = registros;
    const datasFiltradas = datas;
    const series = {
      Lula: registrosFiltrados.map(r => r.candidatos?.Lula ?? null),
      'Flávio': registrosFiltrados.map(r => r.candidatos?.Flávio ?? null)
    };

    const labels = registrosFiltrados.map((_, i) => i + 1);
    const datasets = [];
    const colors = {
      Lula: '#e53935',
      'Flávio': '#43a047'
    };

    const candidatoMap = {
      Lula: 'Lula',
      'Flávio': 'Flávio'
    };

    const todasAsDatas = mediaMovelData.datas.map(d => new Date(d).getTime());
    const minDateMs = Math.min(...todasAsDatas);
    const maxDateMs = Math.max(...todasAsDatas);
    const totalMs = maxDateMs - minDateMs;

    for (const displayName of Object.keys(series)) {
      const jsonKey = candidatoMap[displayName];
      const mmData = mediaMovelData.candidatos[jsonKey];
      if (!mmData) continue;

      const lineData = mmData.media_movel.map((avg, i) => {
        if (avg === null) return null;
        return {
          x: i / (registros.length - 1) * (registros.length - 1),
          y: avg,
          instituto: 'Média móvel',
          data: registros[i].data
        };
      }).filter(d => d !== null);

      datasets.push({
        label: displayName,
        data: lineData,
        borderColor: colors[displayName] || '#666',
        backgroundColor: 'transparent',
        tension: 0.4,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 5,
        borderWidth: 2,
        parsing: { xAxisKey: 'x', yAxisKey: 'y' }
      });

      const pointsData = [];
      for (let i = 0; i < mmData.pesquisas_brutos.length; i++) {
        const val = mmData.pesquisas_brutos[i];
        if (val !== null) {
          const posicaoRelativa = (todasAsDatas[i] - minDateMs) / totalMs * (registros.length - 1);
          pointsData.push({
            x: posicaoRelativa,
            y: val,
            instituto: registrosFiltrados[i].instituto,
            data: registrosFiltrados[i].data
          });
        }
      }

      datasets.push({
        label: `${displayName} (pesquisas)`,
        data: pointsData,
        borderColor: colors[displayName] || '#666',
        backgroundColor: colors[displayName] || '#666',
        showLine: false,
        pointRadius: 4,
        pointHoverRadius: 6,
        parsing: { xAxisKey: 'x', yAxisKey: 'y' }
      });
    }

    const chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        clip: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              filter: (item) => !item.text.includes('(pesquisas)'),
              usePointStyle: true,
              padding: 15,
              font: { size: 12 }
            },
            onClick: (e, item, legend) => {
              const candidateName = item.text;
              const chart = legend.chart;
              const togglePontosSegundo = document.getElementById('toggle-pontos-segundo');
              
              chart.data.datasets.forEach((dataset) => {
                if (dataset.label === candidateName) {
                  // Toggle the main line
                  dataset.hidden = !dataset.hidden;
                } else if (dataset.label === `${candidateName} (pesquisas)`) {
                  // For pesquisas: if main line is becoming hidden, hide pesquisas too
                  // Otherwise, respect the toggle state
                  const mainLineHidden = chart.data.datasets.find(d => d.label === candidateName).hidden;
                  dataset.hidden = mainLineHidden || !togglePontosSegundo.checked;
                }
              });
              chart.update();
            }
          },
          title: { display: false },
          tooltip: {
            mode: 'nearest',
            intersect: false,
            callbacks: {
              title: function(context) {
                if (!context || context.length === 0) return '';
                const raw = context[0].raw;
                if (raw && raw.instituto && raw.data) {
                  const mesesTraducao = {
                    'Jan': 'Janeiro', 'January': 'Janeiro',
                    'Feb': 'Fevereiro', 'February': 'Fevereiro',
                    'Mar': 'Março', 'March': 'Março',
                    'Apr': 'Abril', 'April': 'Abril',
                    'May': 'Maio',
                    'Jun': 'Junho', 'June': 'Junho',
                    'Jul': 'Julho', 'July': 'Julho',
                    'Aug': 'Agosto', 'August': 'Agosto',
                    'Sep': 'Setembro', 'September': 'Setembro',
                    'Oct': 'Outubro', 'October': 'Outubro',
                    'Nov': 'Novembro', 'November': 'Novembro',
                    'Dec': 'Dezembro', 'December': 'Dezembro'
                  };

                  let dataFormatada = raw.data;
                  for (const [abrev, completo] of Object.entries(mesesTraducao)) {
                    const regex = new RegExp(abrev, 'gi');
                    dataFormatada = dataFormatada.replace(regex, completo);
                  }

                  return `${raw.instituto} - ${dataFormatada}`;
                }
                return '';
              },
              label: function(context) {
                let label = context.dataset.label || '';
                label = label.replace(' (pesquisas)', '');
                const value = context.parsed.y;
                if (value !== null) {
                  return `${label}: ${value.toFixed(1)}%`;
                }
                return label;
              }
            }
          }
        },
        scales: {
          x: {
            display: false,
            type: 'linear',
            max: registros.length - 1,
            grid: { display: false }
          },
          y: {
            beginAtZero: false,
            min: 30,
            max: 55,
            title: { display: true, text: 'Votos (%)' },
            grid: { display: false }
          }
        }
      }
    });

    // Armazenar instância do gráfico para controlar pontos
    window.graficoSegundoInstance = chart;

    const timelineStart = document.getElementById('timeline-start-segundo');
    const timelineEnd = document.getElementById('timeline-end-segundo');
    const timelineLabel = document.getElementById('timeline-label-segundo');
    const timelineTrack = document.getElementById('timeline-track-segundo');


    // Only use the actual available date range from the second round data
    const validDates = datasFiltradas.filter(d => d !== null && d !== undefined);
    if (validDates.length === 0) {
      console.error('No valid dates found (2º turno)');
      return;
    }
    // Get the earliest and latest dates from the actual data
    const minDate = new Date(Math.min(...validDates.map(d => d.getTime())));
    const maxDate = new Date(Math.max(...validDates.map(d => d.getTime())));

    function formatDate(date) {
      const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
      return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
    }

    function updateTimelineSegundo() {
      const startPercentage = parseInt(timelineStart.value, 10);
      const endPercentage = parseInt(timelineEnd.value, 10);

      if (startPercentage > endPercentage) {
        if (event.target === timelineStart) {
          timelineEnd.value = startPercentage;
        } else {
          timelineStart.value = endPercentage;
        }
      }

      const actualStart = Math.min(startPercentage, endPercentage);
      const actualEnd = Math.max(startPercentage, endPercentage);

      timelineTrack.style.background = `linear-gradient(to right, #ddd ${actualStart}%, #1565c0 ${actualStart}%, #1565c0 ${actualEnd}%, #ddd ${actualEnd}%)`;

      // Use only the available date range for filtering
      const timeRange = maxDate.getTime() - minDate.getTime();
      const startTime = minDate.getTime() + (timeRange * actualStart / 100);
      const endTime = minDate.getTime() + (timeRange * actualEnd / 100);
      const startDate = new Date(startTime);
      const endDate = new Date(endTime);

      // Filter indices only within the available dates
      const filteredDataIndices = datasFiltradas.map((d, i) => d && d >= startDate && d <= endDate ? i : -1).filter(i => i !== -1);

      for (let datasetIdx = 0; datasetIdx < chart.data.datasets.length; datasetIdx++) {
        const dataset = chart.data.datasets[datasetIdx];
        const isSmoothLine = !dataset.label.includes('(pesquisas)');
        const displayName = isSmoothLine ? dataset.label : dataset.label.replace(' (pesquisas)', '');
        const jsonKey = candidatoMap[displayName];
        const mmData = mediaMovelData.candidatos[jsonKey];
        if (!mmData) continue;
        if (isSmoothLine) {
          const filteredLine = filteredDataIndices
            .map((origIdx, idx) => {
              const avg = mmData.media_movel[origIdx];
              if (avg === null) return null;
              return {
                x: idx / (filteredDataIndices.length - 1 || 1) * (filteredDataIndices.length - 1),
                y: avg,
                instituto: 'Média móvel',
                data: registrosFiltrados[origIdx].data
              };
            })
            .filter(d => d !== null);
          dataset.data = filteredLine;
        } else {
          const filteredPoints = [];
          for (let i = 0; i < filteredDataIndices.length; i++) {
            const origIdx = filteredDataIndices[i];
            const val = mmData.pesquisas_brutos[origIdx];
            if (val !== null) {
              const posicaoRelativa = (filteredDataIndices.length > 1)
                ? i / (filteredDataIndices.length - 1) * (filteredDataIndices.length - 1)
                : 0;
              filteredPoints.push({
                x: posicaoRelativa,
                y: val,
                instituto: registrosFiltrados[origIdx].instituto,
                data: registrosFiltrados[origIdx].data
              });
            }
          }
          dataset.data = filteredPoints;
        }
      }

      timelineLabel.textContent = `${formatDate(startDate)} a ${formatDate(endDate)}`;

      const numFilteredPoints = filteredDataIndices.length;
      chart.options.scales.x.max = numFilteredPoints > 0 ? numFilteredPoints - 1 : 10;
      chart.resize();
      chart.update();
      updateMediaFinalBoxSegundo(filteredDataIndices);
    }

    function updateMediaFinalBoxSegundo(filteredIndices) {
      const mediaFinalItems = document.getElementById('media-final-items-segundo');
      mediaFinalItems.innerHTML = '';

      const candidatos = ['Lula', 'Flávio'];
      const cores = ['#e53935', '#43a047'];
      const partidos = ['PT', 'PL'];
      const nomesJson = ['Lula', 'Flávio'];

      const lastIdx = mediaMovelData.datas.length - 1;

      const dados = [];
      candidatos.forEach((displayName, idx) => {
        const jsonKey = nomesJson[idx];
        const mmData = mediaMovelData.candidatos[jsonKey];

        if (mmData) {
          const lastValue = mmData.media_movel[lastIdx];
          if (lastValue !== null) {
            dados.push({
              nome: displayName,
              partido: partidos[idx],
              valor: lastValue,
              cor: cores[idx]
            });
          }
        }
      });

      dados.sort((a, b) => b.valor - a.valor);

      dados.forEach((d) => {
        const item = document.createElement('div');
        item.className = 'media-item';
        item.innerHTML = `
          <span style="color: ${d.cor}; font-size: 1.2rem;">●</span>
          <span class="media-item-name">${d.nome} (${d.partido})</span>
          <span class="media-item-valor">${d.valor.toFixed(1)}%</span>
        `;
        mediaFinalItems.appendChild(item);
      });
    }

    timelineStart.addEventListener('input', updateTimelineSegundo);
    timelineEnd.addEventListener('input', updateTimelineSegundo);

    updateTimelineSegundo();

    window.addEventListener('resize', () => {
      chart.resize();
    });

    timelineLabel.textContent = `${formatDate(minDate)} a ${formatDate(maxDate)}`;
    updateMediaFinalBoxSegundo(registros.map((_, i) => i));
  } catch (error) {
    console.error('❌ Erro ao montar gráfico 2º turno:', error);
    document.getElementById('graficoVotosSegundo').innerHTML = `<p style="color: red; padding: 20px;">Erro: ${error.message}</p>`;
  }
}
