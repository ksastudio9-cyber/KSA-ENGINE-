# KSA ENGINE

نواة محرك ألعاب إجرائي عربية، حتمية وخفيفة، تحول وصفًا نصيًا واحدًا إلى عالم prototype قابل للتحديث.

## البنية

- `ksa_engine/core.py`: `Vector3`, `Transform`, `Entity`, `GameWorld`, ودورة `Engine`.
- `ksa_engine/text_to_world.py`: مولد عربي/إنجليزي حتمي للتضاريس والمباني والشخصيات والكاميرا والإضاءة والصوت والسينمائية وواجهة المستخدم.
- `ksa_engine/systems.py`: أنظمة الكاميرا والإضاءة والصوت والأنيميشن وتركيب المشهد.
- `ksa_engine/demo.py`: مثال من نص إلى عالم ثم تشغيل لمدة ثانية.
- `cpp/include` و`cpp/src`: نواة C++ مستقلة قابلة للبناء، مناسبة لاحقًا للربط مع renderer أو Python extension.

## التشغيل السريع

```bash
python -m pip install -r requirements-dev.txt
python -m ksa_engine "مدينة صحراوية ليلية فيها واحة ومعركة" --seconds 2 --json
python -m ksa_engine "مدينة صحراوية ليلية فيها واحة ومعركة" --play
python -m ksa_engine --editor
python -m ksa_engine "رجل مخطوف داخل قلعة" --say "سأساعدك وأنقذك" --json
```

## تشغيل سريع من سطح المكتب

تم إنشاء اختصار `KSA ENGINE.desktop` على سطح مكتب Linux، بأيقونة حرف `K`. انقر عليه لفتح محرر صناعة الألعاب. يمكن تشغيله أيضًا من الطرفية:

```bash
./launch_ksa_engine.sh
```

### Windows

على Windows افتح PowerShell داخل مجلد المشروع وشغّل:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows_shortcut.ps1
```

سيظهر اختصار `KSA ENGINE` على سطح مكتب Windows بأيقونة حرف `K`. يمكن تشغيله مباشرة أيضًا عبر:

```powershell
.\launch_ksa_engine.bat
```

المشغّل ينشئ بيئة `.venv` خاصة بالمحرك ويثبت متطلبات التشغيل تلقائيًا، لذلك لا يلوث Python العام. لبناء نسخة قابلة للنقل بصيغة Windows عبر PyInstaller:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

بعد البناء ستجد البرنامج في `dist\KSA ENGINE\KSA ENGINE.exe`. هذه هي طريقة التوزيع المناسبة للكمبيوتر، أما إنشاء ملف `.exe` فعليًا فلا يمكن تنفيذه من حاوية Linux الحالية إلا بعد تشغيل سكربت البناء على Windows.

كما يمكنك النقر مرتين على الملف `تشغيل KSA ENGINE.bat` من مجلد المشروع لتشغيل المحرك مباشرة.
وللتشغيل الأسرع، انقر مرتين على `START_KSA_ENGINE.bat` فقط.

## AI فعلي غير محدود

لجعل الحوار يعتمد على نموذج لغوي حقيقي بدل القواعد الاحتياطية، شغّل Ollama وثبّت نموذجًا ثم عرّف:

```bash
ollama serve
ollama pull llama3.2
export KSA_LLM_BASE_URL=http://127.0.0.1:11434/api
export KSA_LLM_MODEL=llama3.2
python -m ksa_engine "رجل مخطوف داخل قلعة" --say "أريد التفاوض مع الخاطف" --json
```

يمكن أيضًا استخدام أي endpoint متوافق مع OpenAI عبر `KSA_LLM_BASE_URL` و`KSA_LLM_API_KEY`. النموذج يرى وصف العالم وسجل الحوار، ويرجع كلامًا حرًا وأفعالًا آمنة مثل إضافة NPC أو تغيير الهدف. بدون endpoint مضبوط سيظهر اسم المزود `NarrativeAI` كخطة احتياطية، وليس AI عامًا.

في وضع `--play` يعمل renderer منظور 3D: استخدم `WASD` أو الأسهم للحركة و`ESC` للخروج. يتطلب الوضع الرسومي بيئة سطح مكتب أو X/Wayland متاحًا. renderer القديم ثنائي الأبعاد ما زال متاحًا برمجيًا عبر `ksa_engine.pygame_runtime` لأغراض الاختبار.
في وضع `--editor` اكتب وصف العالم، ثم استخدم `GENERATE WORLD` للتوليد، و`PLAY 3D` للتجربة، و`SAVE PROJECT` لحفظ ملف `ksa_project.json`.
في المثال السردي سيضيف المحرك رهينة وخاطفًا وهدف إنقاذ، وستظهر جملة الرهينة تلقائيًا: `تكفى ساعدني!`.

أو باستخدام النواة C++:

```bash
cmake -S . -B build
cmake --build build
./build/ksa_engine_cli "desert city combat" 2
```

## Python

```bash
python -m ksa_engine.demo
python -m pytest
```

مثال:

```python
from ksa_engine import Engine, TextToWorldGenerator
from ksa_engine.systems import AnimationSystem, CameraController

world = TextToWorldGenerator().generate("مدينة صحراوية ليلية فيها واحة ومعركة")
engine = Engine()
engine.add_system(CameraController())
engine.add_system(AnimationSystem())
engine.load_world(world)
engine.run_for(1.0)
```

## C++

```bash
cmake -S . -B build
cmake --build build
```

هذه النسخة أصبحت vertical slice ثلاثي الأبعاد قابلًا للتشغيل، مع renderer منظور برمجي، لكنه ليس بديلًا كاملًا لـ Unreal أو Unity بعد. للوصول إلى مستوى إنتاجي نحتاج GPU backend، أصول PBR، فيزياء، شبكة، محرر، ونظام بناء للمنصات.
