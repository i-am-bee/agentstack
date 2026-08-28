**Katkıda Bulunma Kılavuzu**

## Geliştirme Kurulumu

### Kurulum

Bu proje, araç sürümlerinin (`python`, `uv`, `nodejs`, `pnpm` vb.) yöneticisi olarak [Mise-en-place](https://mise.jdx.dev/) kullanır. Mise, gerekli tüm araçları otomatik olarak indirir; kendiniz kurmanıza gerek yoktur.

Bu projeyi klonlayın ve ardından şu kurulum adımlarını izleyin:

```sh
brew install mise # Daha fazla kurulum yöntemi: https://mise.jdx.dev/installing-mise.html
mise trust
mise install
brew install qemu # Brew kullanmıyorsanız: QEMU'yu başka bir paket yöneticisi aracılığıyla kurun
```

Kurulumdan sonra şunları kullanabilirsiniz:

* `mise run` ile görevleri listeleyip etkileşimli olarak birini seçebilirsiniz.
* `mise <görev-adı>` ile bir görevi çalıştırabilirsiniz.
* `mise x -- <komut>` ile bir proje aracını çalıştırabilirsiniz — örneğin `mise x -- uv add <paket>`.

Eğer `mise x --` ön ekini kullanmadan araçları doğrudan çalıştırmak istiyorsanız, bir shell hook'u etkinleştirmeniz gerekir:

* Bash: `eval "$(mise activate bash)"` (kalıcı hale getirmek için `~/.bashrc` dosyasına ekleyin)
* Zsh: `eval "$(mise activate zsh)"` (kalıcı hale getirmek için `~/.zshrc` dosyasına ekleyin)
* Fish: `mise activate fish | source` (kalıcı hale getirmek için `~/.config/fish/config.fish` dosyasına ekleyin)
* Diğer shell'ler: [belgelere](https://mise.jdx.dev/installing-mise.html#shells) bakın.

### Konfigürasyon

Proje kökündeki `mise.local.toml` dosyasındaki `[env]` bölümünü düzenleyin ([belgeler](https://mise.jdx.dev/environments/)). Dosyayı görmüyorsanız `mise setup` komutunu çalıştırın.

### Platformu Kaynaktan Çalıştırma

CLI kullanarak platformu başlatmak (`agentstack platform start`, hatta `mise agentstack-cli:run -- platform start`) varsayılan olarak **yayınlanmış görüntüleri** kullanır. Yerel görüntüleri kullanmak için bunları oluşturup platforma aktarmanız gerekir.

Bunun yerine şunu kullanın:

```shell
mise agentstack:start
```

Bu, `agentstack-server` ve `agentstack-ui` görüntülerini oluşturacak ve bunları kümeye aktaracaktır. Normalde `agentstack` CLI'sini kullanırken olduğu gibi diğer CLI argümanlarını ekleyebilirsiniz:

```shell
mise agentstack:start --set docling.enabled=true --set oidc.enabled=true 
```

Platformu durdurmak veya silmek için şunları kullanın:

```shell
mise agentstack:stop
mise agentstack:delete
```

Debugging ve Kubernetes'e doğrudan erişim için `KUBECONFIG` ve diğer ortam değişkenlerini ayarlamak için:

```shell
# Ortamı etkinleştir
eval "$(mise run agentstack:shell)"

# Ortamı devre dışı bırak
deactivate
```

### OAuth/OIDC Kimlik Doğrulaması için Yerel Test

Varsayılan olarak, kimlik doğrulama ve yetkilendirme devre dışıdır.

OIDC etkin olarak platformu başlatmak için:

```bash
mise agentstack:start --set auth.enabled=true
```

Bu, Keycloak'ı kurar (kutuda platform kullanıcıları yoktur).

Kullanıcıları <http://localhost:8336> adresinde, admin kullanıcısı (admin:admin dev ortamında) ile oturum açarak ekleyebilirsiniz ve "Yönetim alanları" -> "Kullanıcılar" kısmına gidebilirsiniz.

Kullanıcıları `agentstack-admin` veya `agentstack-developer` rollerini atayarak terfi ettirebilirsiniz. "Kimlik Bilgileri" sekmesinde bir şifre eklemeyi ve e-posta adreslerini doğrulanmış olarak ayarlamayı unutmayın.

Bunu otomatik hale getirmek için `config.yaml` adlı bir dosya oluşturabilirsiniz:

```yaml
auth:
  enabled: true
keycloak:
  auth:
    seedAgentstackUsers:
      - username: admin
        password: admin
        firstName: Admin
        lastName: User
        email: admin@beeai.dev
        roles: ["agentstack-admin"]
        enabled: true
```

Ardından `mise run agentstack:start -f config.yaml` komutunu çalıştırın.

**Mevcut uç noktalar:**

| Servis              | HTTP                                |
|----------------------|-------------------------------------|
| Keycloak             | `http://localhost:8336`             |
| Agent Stack UI       | `http://localhost:8334`             |
| Agent Stack API Docs | `http://localhost:8333/api/v1/docs` |

**OIDC yapılandırması:**

* UI: `apps/agentstack-ui` dizinindeki `template.env` dosyasını takip edin (kopyalayın ve `apps/agentstack-ui/.env` dosyasına yapıştırın).
* Sunucu: `apps/agentstack-server` dizinindeki `template.env` dosyasını takip edin (kopyalayın ve `apps/agentstack-server/.env` dosyasına yapıştırın).

### Bireysel Bileşenleri Çalıştırma ve Hata Ayıklama

Bireysel bileşenleri tam yığın (PostgreSQL, OpenTelemetry, Arize Phoenix vb.) karşısında çalıştırmak ve hata ayıklamak istenir. Bunun için, Kubernetes konteynerini yerel makinenize yeniden yönlendiren [Telepresence](https://telepresence.io/) dahil edilmiştir. (Not: `sshfs` gerekli değildir, çünkü bu kurulumda kullanılmamaktadır.)

```sh
mise run agentstack-server:dev:start
```

Bu, aşağıdakileri yapacaktır:

1. Henüz yoksa `.env` dosyasını oluşturur (burada yapılandırmanızı ekleyebilirsiniz).
2. Varsayılan platform VM'sini ("agentstack") durdurur.
3. Varsayılan olarak kullanılan "agentstack" VM'sinden ayrı bir "agentstack-local-dev" adlı yeni bir VM başlatır.
4. Küme içinde telepresence kurulumunu gerçekleştirir.
   > Not: Bu, bir ağ yığını kurmak için **root erişimi** gerektirecektir.
5. Kümedeki agentstack'ı değiştirir ve gelen tüm trafiği localhost'a yönlendirir.

Komut başarılı olduktan sonra:

* Makineniz, kümede çalışıyormuş gibi istekte bulunabilir. Örneğin:
  `curl http://<service-name>:<service-port>`.
* PostgreSQL'e varsayılan kimlik bilgileri `postgresql://agentstack-user:password@postgresql:5432/agentstack` ile bağlanabilirsiniz.
* Şimdi sunucunuzu IDE'nizden veya `mise run agentstack-server:run` komutunu kullanarak **18333** portunda başlatabilirsiniz.
* Agentstack-cli'yi `mise agentstack-cli:run -- <komut>` veya localhost:8333 veya localhost:18333'e HTTP istekleri ile çalıştırabilirsiniz.
  * localhost:8333, kümeden port yönlendirilmiştir, bu nedenle herhangi bir istek, küme ağından geçerek agentstack pod'una ulaşacak ve bu pod, telepresence ile değiştirilerek tekrar yerel makinenize yönlendirilecektir.
  * localhost:18333, yerel platformunuzun çalışması gereken yerdir.

Küme içeriğini `kubectl` veya `k9s` ve lima kullanarak incelemek için geliştirme ortamını etkinleştirin:

```shell
# Geliştirme ortamını etkinleştir
eval "$(mise run agentstack-server:dev:shell)"

# Geliştirme ortamını devre dışı bırak
deactivate
```

İşiniz bittiğinde, geliştirme kümesini ve ağı durdurmak için şunları kullanabilirsiniz:

```shell
mise run agentstack-server:dev:stop
```

Veya küme tamamen silmek için:

```shell
mise run agentstack-server:dev:delete
```

> İPUCU: Eğer uyku sonrası veya uzun bir süre hareketsiz kaldıktan sonra bağlantı sorunlarıyla karşılaşırsanız, önce `mise run agentstack-server:dev:reconnect` komutunu deneyin. Tüm VM'yi temizleyip yeniden başlatmanız gerekebilir.

#### Test Geliştirme

Yerel olarak agentstack-server testlerini çalıştırmak ve geliştirmek için yukarıdaki `mise run agentstack-server:dev:start --set auth.enabled=true` komutunu kullanın.

> Not:
>
> * Bazı testler ek ayarlar gerektirir (örneğin, kimlik doğrulamayı etkinleştirmek), daha fazla bilgi için `template.env` dosyasındaki testler bölümüne bakın.
> * Testler veritabanınızı sıfırlayabilir - ajanları yeniden eklemeniz veya modeli yeniden yapılandırmanız gerekebilir.

Yerel olarak, testler için varsayılan model `apps/agentstack-server/tests/conftest.py` dosyasında yapılandırılmıştır (`llama3.1:8b` ollama'dan). Bu modelin yerel olarak çalıştığından emin olun.

<details>
<summary> Daha Düşük Seviyeli Ağ Kullanımı ile Telepresence Doğrudan Kullanma </summary>

```shell
# Ortamı etkinleştir
eval "$(mise run agentstack-server:dev:shell)"

# Platformu başlat
mise agentstack-cli:run -- platform start --vm-name=agentstack-local-dev # isteğe bağlı --tag [etiket] --import-images
mise x -- telepresence helm install
mise x -- telepresence connect

# Bir pod'a trafiği almak için onu kümede değiştirin
mise x -- telepresence replace <pod-adı>

# Değiştirme/engelleme/girişin nasıl çalıştığı hakkında daha fazla bilgi: https://telepresence.io/docs/howtos/engage

# İşiniz bittiğinde Telepresence'i kapatmak için:
mise x -- telepresence quit
```

</details>

#### Ollama

Bu yerel kurulumu Ollama ile çalıştırmak istiyorsanız, LLM'yi kurarken özel bir seçenek kullanmalısınız:

```
agentstack model setup --use-true-localhost
```

### Örnekler

`examples/` dizinindeki örnekler, bağımsız ajanlar, belge kod örnekleri ve e2e testleri olarak hizmet eder. Tam detaylar için [`examples/README.md`](examples/README.md) dosyasına bakın.

`examples/` klasör yapısı, belgelerin yapısını yansıtır. Örneğin, `docs/development/agent-integration/forms.mdx` dosyasında kullanılan örnekler `examples/agent-integration/forms/` altında bulunur. Her belge bölüm başlığı, bir örnek adını eşler (örneğin "İlk Formun Render Edilmesi" -> `initial-form-rendering`).

**Mevcut bir örneği değiştirme:**

1. Ajan kodunu `examples/<path>/src/<name>/agent.py` dosyasında düzenleyin.
2. İlgili e2e testini çalıştırın: `apps/agentstack-server/tests/e2e/examples/<path>/test_<name>.py`.
3. Entegre edilmiş kodu senkronize etmek için belgeleri güncelleyin: `mise run docs:fix`.

**Yeni bir örnek oluşturma:**

```bash
mise run example:create <path> <description>
```

Bu, örnek ajanı ve e2e testini oluşturur. Oluşturma işleminden sonra:

1. Ajan mantığını `examples/<path>/src/<name>/agent.py` dosyasında uygulayın.
2. E2e testini `apps/agentstack-server/tests/e2e/examples/<path>/test_<name>.py` dosyasında uygulayın.
3. Örneği belgelerde embedme etiketleri kullanarak gömün:
   ```mdx
   {/* <!-- embedme examples/<path>/src/<name>/agent.py --> */}
   ```
4. Belgelerde gömülü kodu senkronize etmek için `mise run docs:fix` komutunu çalıştırın.

> **İsimlendirme kuralı:** Şablon, ajan işlevini `<snake_case_name>_example` olarak adlandırır (örneğin, `initial_form_rendering_example`). Örnek adı, kullanıldığı belge bölüm başlığından türetilir (örneğin "İlk Formun Render Edilmesi" -> `initial-form-rendering`).

**E2e örnek testlerini çalıştırma:**

| Komut | Ne çalıştırır |
|---|---|
| `mise run agentstack-server:test:e2e` | Ana e2e testleri (örnekler hariç) |
| `mise run agentstack-server:test:e2e-examples` | Örnek e2e testleri yalnızca |

E2e örnek testleri **ana e2e setinin** bir parçası değildir ve her taahhütte çalışmaz. `main` dalına birleştirildiğinde veya `e2e-examples` etiketini eklediğinizde PR'larda otomatik olarak çalıştırılır.

### Göçlerle Çalışma

Aşağıdaki komutlar geliştirme ortamında göç oluşturmak veya çalıştırmak için kullanılabilir:

* Göçleri çalıştır: `mise run agentstack-server:migrations:run`
* Göçleri oluştur: `mise run agentstack-server:migrations:generate`
* Alembic komutunu doğrudan kullan: `mise run agentstack-server:migrations:alembic`

> NOT: Geliştirme kurulumu, yerel olarak oluşturulan görüntüyü çalıştıracak ve onu yerel örneğinizle değiştirmeden önce göçlerini çalıştıracaktır. Yeni uyguladığınız göçler çalışmıyorsa, geliştirme kurulumu düzgün başlamayacak ve önce göçleri düzeltmeniz gerekecektir. Shell'i etkinleştirmek için `eval "$(mise run agentstack-server:dev:shell)"` komutunu kullanabilir ve en sevdiğiniz Kubernetes IDE'sini (örneğin, k9s veya kubectl) kullanarak göç günlüklerini görebilirsiniz.

### Bireysel Bileşenleri Çalıştırma

Agent Stack bileşenlerini geliştirme modunda (doğru yeniden inşa sağlamak için) çalıştırmak için aşağıdaki komutları kullanın.

#### Sunucu

Sunucuyu [Kaynaktan Platformu Çalıştırma](#running-the-platform-from-source) bölümünde açıklanan kurulumla oluşturun ve çalıştırın.
Ya da [Bireysel Bileşenleri Çalıştırma ve Hata Ayıklama](#running-and-debugging-individual-components) bölümünde açıklanan geliştirme kurulumunu kullanın.

#### CLI

```sh
mise agentstack-cli:run -- agent list
mise agentstack-cli:run -- agent run website_summarizer "summarize beeai.dev"
```

#### UI

```sh
# UI geliştirme sunucusunu çalıştır:
mise agentstack-ui:run

# UI ayrıca agentstack-server'dan (statik modda) da kullanılabilir:
mise agentstack-server:run
```

## Yayınlama

Agent Stack, bir sonraki sürüm geliştirmesi için `main` dalını ve kararlı sürümler için `release-v*` dallarını kullanmaktadır.

Yayın süreci üç adımdan oluşur:

### Adım 1: Yayını Kesin

`main` dalında ayarlanmış mevcut sürümün istenen yayın sürümü olduğundan emin olun. Değilse, önce `mise run release:set-version <new-version>` komutunu çalıştırın.

`main` dalından `release:new` görevini çalıştırın:

```shell
mise run release:new
```

Bu, yeni bir `release-vX.Y` dalı oluşturacak (main'deki sürüm numarası ile) ve `main` dalındaki sürümü bir sonraki yamanın sürümüne (örneğin, `1.2.3` -> `1.2.4`) yükseltecektir.

### Adım 2: Yayın Dalında QA ve Yayını Polonya

Yayın dalında yayını iteratif olarak parlatabilirsiniz. Hem yayın dalında hem de `main` dalında ilgili düzeltmeleri uygulamayı unutmayın, örneğin `git cherrypick` ile.

Yayın dalından bir yayın adayını yayınlamak için `mise run release:publish-rc` komutunu çalıştırın. Bu, `X.Y.Z-rcN` sürümünü yayınlayacaktır; burada `N`, her RC yayınında artırılır.

Yeni bir RC oluşturmak, test için paketinin ön sürümünü dağıtmak üzere GH eylemini tetikleyecektir.

### Adım 3: Yayınla

RC QA turlarını tamamladıktan sonra, yayın dalından nihai yayını yayınlayın:

```shell
mise run release:publish-stable
```

Bu işlem, kararlı sürümü yayınlamanın yanı sıra, `main` dalındaki belgelerin yeni sürümü yansıtacak şekilde güncellenmesini de sağlar; bu, yayın dalındaki `docs/development` klasörünü `main` dalındaki `docs/stable`'a taşımakla gerçekleşir.

## Belgeler

İki belge klasörü vardır: `docs/stable` ve `docs/development`. Mintlify'nin doğası gereği, belgeler `main` dalından dağıtılır, bu nedenle `docs/stable`'ı en son kararlı sürümü temsil edecek şekilde donduruyoruz. **Sadece belgelerdeki sorunları düzeltmek için `docs/stable` içinde manuel değişiklikler yapın, özellik PR'ları yalnızca `docs/development`'ı düzenlemelidir.**

Tüm PR'ler **ya** `docs/development` içinde ilgili belgeleri iç
