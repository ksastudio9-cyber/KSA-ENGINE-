# KSA ENGINE

نواة محرك ألعاب إجرائي عربية، حتمية وخفيفة، تحول وصفًا نصيًا واحدًا إلى عالم prototype قابل للتحديث.

## البنية

- `ksa_engine/core.py`: `Vector3`, `Transform`, `Entity`, `GameWorld`, ودورة `Engine`.
- `ksa_engine/text_to_world.py`: مولد عربي/إنجليزي حتمي للتضاريس والمباني والشخصيات والكاميرا والإضاءة والصوت والسينمائية وواجهة المستخدم.
- `ksa_engine/systems.py`: أنظمة الكاميرا والإضاءة والصوت والأنيميشن وتركيب المشهد.
- `ksa_engine/demo.py`: مثال من نص إلى عالم ثم تشغيل لمدة ثانية.
- `cpp/`: runtime أصلي بلغة C++17 وCLI مستقل لتوليد العالم وتشغيله دون Python.

## التشغيل السريع

```bash
python -m pip install -r requirements-dev.txt
python -m ksa_engine "مدينة صحراوية ليلية فيها واحة ومعركة" --seconds 2 --json
python -m ksa_engine "مدينة صحراوية ليلية فيها واحة ومعركة" --play
python -m ksa_engine --editor
python -m ksa_engine "رجل مخطوف داخل قلعة" --say "سأساعدك وأنقذك" --json
```

## تشغيل سريع من سطح المكتب

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

بعد البناء ستجد البرنامج المستقل في `dist\KSA.exe`. هذا الملف يفتح المحرر مباشرة بالنقر المزدوج، ولا يحتاج Python أو Pip أو VS Code على جهاز المستخدم. لا يمكن إنشاء Windows `.exe` فعليًا من حاوية Linux الحالية؛ شغّل سكربت البناء على Windows.

يمكنك أيضًا بناء الملف بدون جهاز Windows عبر GitHub Actions: افتح تبويب `Actions` في المستودع، اختر `Build Windows EXE` ثم اضغط `Run workflow`. بعد نجاح المهمة نزّل artifact باسم `KSA-windows` وستجد بداخله `KSA.exe`.

يبني `build_windows.ps1` runtime C++ عبر CMake، ثم يضمّه مع Python وpygame وموارد المحرك في ملف واحد باسم `ksa.exe`. أوامر النص وJSON تستخدم runtime C++، بينما يبقى `--editor` و`--play` و`--say` على Python لأنها تحتاج واجهة pygame أو تكامل LLM.

لبناء runtime C++ محليًا على Linux أو Windows:

```bash
cmake -S cpp -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
ctest --test-dir build/native --output-on-failure
```

بعد البناء، انقر مرتين على `dist\KSA.exe` لتشغيل المحرر مباشرة.

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

في وضع `--play` يعمل العرض ثلاثي الأبعاد: استخدم `WASD` أو الأسهم للحركة و`ESC` للخروج. يتطلب الوضع الرسومي بيئة سطح مكتب متاحة.
في وضع `--editor` اكتب وصف العالم، ثم استخدم `GENERATE WORLD` للتوليد، و`PLAY 3D` للتجربة، و`SAVE PROJECT` لحفظ ملف `ksa_project.json`.
في المثال السردي سيضيف المحرك رهينة وخاطفًا وهدف إنقاذ، وستظهر جملة الرهينة تلقائيًا: `تكفى ساعدني!`.

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

هذه النسخة أصبحت نموذجًا ثلاثي الأبعاد قابلًا للتشغيل مع محرر لصناعة الألعاب.
