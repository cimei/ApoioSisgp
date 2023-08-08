# Botão

Botões de ação. Aplicável em tags interativas, tais como `<a href="">`, `<button>`, `<input type="submit">` etc.

## Dependências

Nenhuma dependência.

## Código básico

```html
<button class="br-button" type="button">Botão</button>
```

## Detalhamento

Este componente é formado pelos seguintes elementos:

- `br-button`: container do componente

## Variações

Estão disponíveis 9 tipos de botões. Cada tipo é aplicado com o prefixo `is-`.

4 para uso comum:

- Primário
- Secundário
- Terciário
- Cancelar

5 para uso específico:

- Call to Action
- Circular
- Redes Sociais
- Voltar ao Topo
- Filtrar

### Botão Primário

Toda **ação principal** na tela deve usar o **Botão Primário**.

NUNCA use mais de 1 Botão Primário, pois confunde o usuário em sua tomada de decisão.

Exemplo de uso:

```html
<button class="br-button is-primary" type="button">Ação</button>
```

### Botão Secundário

Para **ações subjetivas** ou de **menor importância** use **Botão Secundário**. Este botão PODE ser usado quantas vezes forem necessárias na tela.

Exemplo de uso:

```html
<button class="br-button is-secondary" type="button">Ação</button>
```

### Botão Terciário

Nas situações em que o botão deverá se comportar como um **link** use o **Botão Terciário**.

Exemplo de uso:

```html
<button class="br-button is-tertiary" type="button">Ação</button>
```

### Botão Cancelar

Para cancelar use o **Botão Cancelar**.

Cor no botão sinaliza uma chamada à ação, por isso o **Botão Cancelar** possui a mesma cor de um texto padrão na tela. Além disso, é preciso passar a impressão de que o botão não fará alterações no sistema e será sua fuga da ação.

[https://uxmovement.com/buttons/why-cancel-buttons-should-never-have-a-color/](https://uxmovement.com/buttons/why-cancel-buttons-should-never-have-a-color/)

Exemplo de uso:

```html
<button class="br-button is-cancel" type="button">Cancelar</button>
```

### Botão Call to Action

Usado em situações que necessitem atenção especial. Ele é diferente do Botão Primário.

Exemplo de uso:

```html
<button class="br-button is-call-to-action" type="button">Ação</button>
```

### Botão Circular

Use apenas ícones nestes botões.

O ícone pode ser uma imagem - `<img src="" alt="">` ou ícone do Fontawesome - `<i class="fas">`.

Imagens serão redimencionadas automaticamente dentro do botão. Nos ícones do Fontawesome use **cor primária** ou **cor secundária**.

Para conhecer os ícones do Fontawesome veja o link [https://fontawesome.com/](https://fontawesome.com/).

Exemplo de uso:

```html
<button class="br-button is-circle" type="button">
  <img class="icon" src="image.png" alt="Texto descritivo">
</button>
<button class="br-button is-circle is-primary" type="button">
  <i class="fas fa-chevron-up"></i>
</button>
<button class="br-button is-circle is-secondary" type="button">
  <i class="fas fa-chevron-down"></i>
</button>
```

### Botão Redes Sociais

Botões para login com redes sociais. A regra é a mesma dos botões circulares.

A maioria dos ícones de redes sociais podem ser encontrados no Fontawesome. Para ícones mais complexos, como o do Google, use imagem.

Exemplo de uso:

```html
<button class="br-button is-social-media is-facebook" type="button">
  <i class="fab fa-facebook-f fa-lg"></i>
</button>
<button class="br-button is-social-media is-twitter" type="button">
  <i class="fab fa-twitter fa-lg"></i>
</button>
<button class="br-button is-social-media" type="button">
  <img src="imagem" alt="Texto descritivo">
</button>
```

### Botão Voltar ao Topo

Usado geralmente ao final de conteúdos para facilitar a rolagem de tela.

Um script deve ser aplicado ao botão para realizar a ação.

Exemplo de uso:

```html
<button class="br-button is-go-top" type="button" onclick="topFunction()">
  Voltar ao topo
  <span class="br-button is-circle is-primary">
    <i class="fas fa-chevron-up"></i>
  </span>
</button>
<script>
  function topFunction() {
    document.body.scrollTop = 0; // Safari
    document.documentElement.scrollTop = 0; // Chrome, Firefox, IE, Opera
  }
</script>
```

### Botão Filtrar

Usado especial para uso de filtros.

Exemplo de uso:

```html
<button class="br-button is-filter" type="button">
  Filtrar
  <i class="fas fa-sliders-h"></i>
</button>
```

## Estados

### `focus` e `hover`

- São aplicados automaticamente no elemento
- Podem ser aplicados diretamente usando o prefixo `is-`

Exemplo de uso:

```html
<button class="br-button is-primary is-hover" type="button">Ação</button>
<button class="br-button is-primary is-focus" type="button">Ação</button>
```

### disabled

- Deve ser aplicado como propriedade no componente quando for tag do tipo `<button>` ou `<input>`
- Pode ser aplicado diretamente usando o prefixo `is-`, porém a aplicação por classe apenas modifica o estilo e não desabilita o componente de fato

Exemplo de uso:

```html
<button class="br-button is-primary" type="button" disabled>Ação desativada</button>
<a href="" class="br-button is-primary is-disabled">Ação</a>
```

### loading

- Sempre que necessário aplique o estado de `loading` nos botões para sinalizar ao usuário que o sistema está operando
- Este estado é recomendados para os tipos **Botão Primário**, **Botão Secundário**, **Botão Call to Action** e **Botão Circular**
- Deve ser aplicado diretamente no componente usando o prefixo `is-`

Exemplo de uso:

```html
<button class="br-button is-primary is-loading" type="button">Ação</button>
```

## Regras especiais

Em _smartphones_ o botão terá a largura da tela. Será aplicado espaçamento vertical automático de 16px entre eles.

Nos demais dispositivos os botões terão tamanho mínimo de 144px. Será aplicado espaçamento horizontal automático de 24px entre botões.

Botões dentro do elemento `actions` do componente `br-form` serão ordenados de forma inversa.
