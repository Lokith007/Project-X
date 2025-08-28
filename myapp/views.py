import base64, time
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.timezone import now, localtime
from datetime import timedelta
from django.db.models import F, Avg
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login,logout,authenticate
from django.urls import reverse, reverse_lazy
from django.views import View
from .forms import RegistrationForm, EditProfileForm,OrganizationForm, EditEducationForm, EditExperienceForm, PostForm, UserProjectForm, EditSkillForm, EditCurrentPositionForm, EditOrgForm, Postsignup_infoForm
from mindlogs.forms import MindLogForm
from django.contrib.auth.models import User
from .models import userinfo, projects, Domain, skill, project_comment, project_reply, user_status, organization, SavedItem, education, post, post_comments, user_project, event, current_position, event_comment, event_reply, experience, Notification, Industry, follow
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger
from django.db.models import Q
from django.template.loader import render_to_string
from itertools import groupby
from .algorithms import get_explore_users, get_personalized_feed, top_skills_list
from allauth.account.views import PasswordChangeView
from django.contrib import messages
from .utils import send_notification_email, verified_user_ids
from datetime import date, timedelta
from collections import Counter, defaultdict

#Logs
from mindlogs.utils import get_24h_mindlog_stats, streak_calculation
from mindlogs.models import MindLog
from mindlogs.views import get_max_streak, build_contribution_months

# Create your views here.
class CustomPasswordChangeView(PasswordChangeView):
    # Redirect to this URL after a successful password change
    success_url = reverse_lazy('index')

@login_required
def post_login_check(request):
    user_info = request.user.info
    if user_info.needs_profile_completion:
        return redirect('signup_about', uuid=user_info.uuid)
    return redirect('/')

#Auth:
class sign_up(View):
    def get(self, request):
        form = RegistrationForm()
        context = {
            'form': form
        }
        return render(request, 'registration/sign_up.html', context)
    
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            userinfo.objects.create(user=user)
            current_position.objects.create(user = user.info)
            education.objects.create(user = user.info)
            SavedItem.objects.create(user = user.info)
            # user.save()
            
            username = form.cleaned_data.get("username") #Authenticate the user:
            password = form.cleaned_data.get("password1")
            email = form.cleaned_data.get("email")
            user = authenticate(username = username, password=password)
            if user is not None:
                login(request, user) # Log the user in
                print(user)
                reverse_url = reverse("signup_about", args=[user.info.uuid])
                return redirect(reverse_url)
        context = {
            'form': form
        }
        return render(request, 'registration/sign_up.html', context)
        
@login_required
def signup_about(request, uuid):
    if request.method == 'POST':
        userinfo_obj = request.user.info
        bio_input = request.POST.get('bio', '')
        userinfo_obj.bio = bio_input.replace('\n', ' ').replace('\r', '').strip()
        userinfo_obj.linkedin =request.POST.get('linkedin')
        userinfo_obj.website = request.POST.get('website')
        userinfo_obj.stackoverflow = request.POST.get('stackoverflow')
        userinfo_obj.github = request.POST.get('github')
        userinfo_obj.save()
        reverse_url = reverse("signup_character", args=[userinfo_obj.uuid])
        return redirect(reverse_url)
    context = {}
    return render(request, 'myapp/signup-about.html', context)

@login_required
def signup_character(request, uuid):
    form = Postsignup_infoForm(instance=request.user.info)
    if request.method == 'POST':
        form = Postsignup_infoForm(request.POST, instance=request.user.info)
        if form.is_valid():
            form.save()
            reverse_url = reverse("signup_skills", args=[request.user.info.uuid])
            return redirect(reverse_url)
    context = {
        'form': form
    }
    return render(request, 'myapp/signup-character.html', context)

@login_required
def signup_skills(request, uuid):
    skill_form = EditSkillForm(instance=request.user.info)
    if request.method == 'POST':
        skill_form = EditSkillForm(request.POST, instance=request.user.info)
        if skill_form.is_valid():
            request.user.info.needs_profile_completion = False
            request.user.info.save()
            skill_form.save()
            return redirect('/')
    context = {
        'form': skill_form
    }
    return render(request, 'myapp/signup-selectskill.html', context)

def contribute_page(request):
    return render(request, 'myapp/contribute.html')

def feedback_page(request):
    return render(request, 'myapp/feedback.html')

# @login_required
def index(request):
    if not request.user.is_authenticated:
        return render(request, 'myapp/landing_page.html')
    
    if request.user.info.needs_profile_completion:
        return redirect('signup_about', uuid=request.user.info.uuid)
    type = request.GET.get('feed', "all")
    page = 1 
    feed_page = get_personalized_feed(request, type=type, page=page, per_page=7)
    followed_orgs = request.user.info.followed_organization.all() | request.user.organization.all()
    followed_orgs = followed_orgs.distinct() 
    tot_upcoming_events = event.objects.filter(organization__in=followed_orgs, start_date__gte=timezone.now()).count()
    post_form = PostForm()
    logform = MindLogForm()
    mindlog_obj = get_24h_mindlog_stats()
    context = {
        'active_home': True,
        'post_form': post_form,
        'logform': logform,
        'feed_items': feed_page,
        'tot_upcoming_events': tot_upcoming_events,
        'mindlog_obj': mindlog_obj,
        'type': type,
    }
    return render(request, 'myapp/index.html', context) 

@login_required
def load_more_feed(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    page = int(request.GET.get('page', 1))
    type = request.GET.get('feed', 'all')

    suggested_peoples = get_explore_users(filter_dev=userinfo.objects.all(), request=request, count=7, order_by='?')
    offset = (page - 1) * 10
    feed_page = get_personalized_feed(request, type=type, page=page, per_page=7)
    print(feed_page)
    html = render_to_string('myapp/feed_items.html', {'feed_items': feed_page, 'suggested_peoples': suggested_peoples, 'offset': offset}, request=request)

    return JsonResponse({
        'html': html,
        'has_next': feed_page.has_next()
    })

@login_required
def notification_page(request):
    post_form = PostForm()
    base_notifications = Notification.objects.filter(user=request.user.info).order_by('-created_at')
    unread_count = base_notifications.filter(is_read=False).count()
    notifications = base_notifications[:70]
    # Group notifications by time
    today = localtime(now()).date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    grouped_notifications = {
        "Today": [],
        "Yesterday": [],
        "This Week": [],
        "Older": []
    }

    for notification in notifications:
        notification_date = localtime(notification.created_at).date()

        if notification_date == today:
            grouped_notifications["Today"].append(notification)
        elif notification_date == yesterday:
            grouped_notifications["Yesterday"].append(notification)
        elif notification_date >= week_ago:
            grouped_notifications["This Week"].append(notification)
        else:
            grouped_notifications["Older"].append(notification)
                  
    # Mark unread notifications as read after viewing 
    Notification.objects.filter(user=request.user.info, is_read=False).update(is_read=True)
    context = {
        "grouped_notifications": grouped_notifications,
        "post_form": post_form,
        'notification_count': unread_count
    }
    return render(request, 'myapp/notification.html', context)

@login_required
def get_notification_count(request):
    unread_count = Notification.objects.filter(user=request.user.info, is_read=False).count()
    return JsonResponse({"unread_count": unread_count})

#profile-page
@login_required
def user_profile(request, user_name):
    userinfo_obj = get_object_or_404(userinfo, user__username = user_name)
    user_project = user_created_project = post_qs= link_available = open_exp_flag = open_edu_flag = open_editprofile_flag = open_project_flag =editprofile_form = edu_form = exp_form = project_form = skill_form  = False
    social_links = { 
    'github': userinfo_obj.github if userinfo_obj.github else None,
    'linkedin': userinfo_obj.linkedin if userinfo_obj.linkedin else None,
    'stack-overflow': userinfo_obj.stackoverflow if userinfo_obj.stackoverflow else None,
    'website': userinfo_obj.website if userinfo_obj.website else None
}
    if social_links.get('github') or social_links.get('linkedin') or social_links.get('stackoverflow') or social_links.get('website'):
        link_available = True
    skill_list = userinfo_obj.skills.all()
    exp_obj = userinfo_obj.experiences.all().order_by('-start_date')
    post_form = PostForm()
    
    #streak and other logs calculations
    logs = MindLog.objects.filter(user = userinfo_obj).order_by("-timestamp")
    
    total_logs = logs.count()
    last_log_date = timezone.localtime(logs.first().timestamp).date() if total_logs else None
    
    avg_latency = int(logs.aggregate(avg=Avg('latency'))['avg']) if total_logs else 0 # Avg Latency
    colors = list(logs.exclude(neuro_color__isnull=True).values_list('neuro_color', flat=True)) 
    top_color = Counter(colors).most_common(1)[0][0] if colors else None #color vibe
    clone_impact = MindLog.objects.filter(original_log__user=userinfo_obj).count()  #total clone count
    
    streak_count = streak_calculation(logs)
    max_streak_count = get_max_streak(logs)
    
    year = int(request.GET.get('year', timezone.now().year))
    log_heat_map = logs.filter(
        timestamp__year=year
    ).values_list('timestamp', flat=True)

    log_map = defaultdict(int)
    for ts in log_heat_map:
        date_str = timezone.localtime(ts).strftime('%Y-%m-%d')
        log_map[date_str] += 1

    # Prepare full 1-year grid
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    total_days = (end_date - start_date).days + 1

    contribution_days = []
    for i in range(total_days):
        current_day = start_date + timedelta(days=i)
        contribution_days.append({
            'date': current_day.strftime('%Y-%m-%d'),
            'count': log_map.get(current_day.strftime('%Y-%m-%d'), 0)
        })
        
    contribution_months = build_contribution_months(contribution_days)
    log_year_count =  sum(log_map.values())
    years_available = logs.dates('timestamp', 'year')
    
    #latest 5 logs 
    mindlogs = logs[:5]
    
    section = request.GET.get('section', 'overview') 
    print(section)
        
    if section == 'posts':
        post_qs = post.objects.filter(user = userinfo_obj).order_by('-created_at')
    
    is_following = request.user.info.is_following(userinfo_obj)
    # Suggested Project
    suggested_project = projects.objects.filter(skill_needed__in = request.user.info.skills.all()).distinct().order_by('-created_at')[:5]
    if not suggested_project:
        suggested_project = projects.objects.all().order_by('-created_at')[:5] #For user, with no skill    
    if request.user.info == userinfo_obj: #Edit options
        edu_form = EditEducationForm(instance=request.user.info.education)
        exp_form = EditExperienceForm()
        editprofile_form = EditProfileForm(instance=request.user.info)
        project_form = UserProjectForm()
        skill_form = EditSkillForm(instance=request.user.info)
    else:
        session_key = f'user_viewed_{user_name}'
        if not request.session.get(session_key, False):
            userinfo.objects.filter(user__username=user_name).update(profile_views=F('profile_views') + 1)
            request.session[session_key] = True
        
    if request.method == 'POST' and userinfo_obj == request.user.info:
        form_type = request.POST.get('form_type')
        if form_type == 'experience':
            exp_form = EditExperienceForm(request.POST)
            if exp_form.is_valid():
                form = exp_form.save(commit=False)
                form.user = request.user.info
                form.save()
                exp_form = EditExperienceForm()
            else:
                open_exp_flag = True
        elif form_type == 'education':
            action = request.POST.get('action')
            if action == 'save':
                edu_form = EditEducationForm(request.POST, instance=request.user.info.education)
                if edu_form.is_valid():
                    edu_form.save()
                else:
                    open_edu_flag = True
                    print("Form errors:", edu_form.errors)
            elif action == 'delete':
                request.user.info.education.delete()
                education.objects.create(user = request.user.info)
                redirect_url = reverse("user_profile", args=[request.user.username])
                return redirect(f"{redirect_url}?section=info")
                
        elif form_type == 'editprofile':
            editprofile_form = EditProfileForm(request.POST, request.FILES, instance = request.user.info)
            if editprofile_form.is_valid():
                userinfo_obj = editprofile_form.save(commit=False)
                cropped_image_data = request.POST.get('croppedImage', '')
                if cropped_image_data:
                    try:
                        format, imgstr = cropped_image_data.split(';base64,')
                        ext = format.split('/')[-1]
                        image_data = base64.b64decode(imgstr)
                        file_name = f"{request.user.username}_profile.{ext}"
                        userinfo_obj.profile_image = ContentFile(image_data, name=file_name)
                    except (ValueError, base64.binascii.Error):
                        editprofile_form.add_error(None, "Invalid image data. Please upload a valid image.")
                        open_editprofile_flag = True
                userinfo_obj.save()
                redirect_url = reverse("user_profile", args=[request.user.username])
                return redirect(redirect_url)
            else:
                open_editprofile_flag = True
        elif form_type == 'skill':
            skill_form = EditSkillForm(request.POST, instance=request.user.info)
            if skill_form.is_valid():
                skill_form.save()
                redirect_url = reverse('user_profile', args=[request.user.username])
                return redirect(f'{redirect_url}?section=info')  
                
    context = {
        'userinfo_obj': userinfo_obj,
        'social_links': social_links,
        'link_available': link_available,
        'exp_obj': exp_obj,
        'section': section,
        'is_following': is_following,
        'user_project': user_project,
        'user_created_project': user_created_project,
        'post_qs': post_qs,
        'suggested_project': suggested_project,
        'ep_form': editprofile_form,
        'edu_form': edu_form,
        'exp_form': exp_form,
        'post_form': post_form,
        'skill_form': skill_form,
        'project_form': project_form,
        'skill_list': skill_list,
        'profile_type': 'user',
        'flag': {'open_edu_flag': open_edu_flag, 'open_exp_flag': open_exp_flag, 'open_editprofile_flag': open_editprofile_flag, 'open_project_flag': open_project_flag},

        'streak_count': streak_count,
        'max_streak_count': max_streak_count,
        'log_map': dict(log_map),
        'year': year,
        'years_available': years_available,
        'contribution_months': contribution_months,
        'log_year_count': log_year_count,
        'total_logs': total_logs,
        'last_log_date': last_log_date,
        'avg_latency': avg_latency,
        'top_color': top_color,
        'clone_impact': clone_impact,
        'mindlogs': mindlogs
    }
    return render(request, 'myapp/user_profile_v2.html', context)

#follow request:
@login_required
def unfollow_user(request, otheruserinfo_id):
    otheruser = userinfo.objects.get(id = otheruserinfo_id)
    user = request.user.info
    if user != otheruser:
        user.unfollow(otheruser)
        Notify_obj = Notification.objects.filter(user=otheruser, sender=user, notification_type="follow")
        if Notify_obj:  
            Notify_obj.delete()
        return JsonResponse({"status": "unfollowed", "message": "User unfollowed Successfully.", 'followers_count': otheruser.get_followers().count(), 'following_count': otheruser.get_following().count()})
    return JsonResponse({"status":"error", "message": "Invalid request."}, status = 400)

@login_required
def follow_user(request, otheruserinfo_id):
    otheruser = userinfo.objects.get(id = otheruserinfo_id)
    user = request.user.info
    if user != otheruser:
        user.follow(otheruser)
        notify = Notification.objects.create(user=otheruser, sender=user, notification_type="follow")
        send_notification_email(otheruser, f'🧑‍💻 {user.user.username} {notify.get_notification_type_display()}!')
        return JsonResponse({"status": "followed", "message": "User followed successfully.", 'followers_count': otheruser.get_followers().count(), 'following_count': otheruser.get_following().count()})
    return JsonResponse({"status": "error", "message": "Invalid request."}, status=400)
    
@login_required
def follow_list(request, username):
        userinfo_obj = userinfo.objects.get(user__username = username) #user-profile list
        post_form = PostForm()
        l = request.GET.get('list')
        grp = False
        if l == None:
            return HttpResponseRedirect(f'{request.path}?list=followers')
        if l == 'followers':
            list = userinfo_obj.get_followers()
        elif l == 'following':   
            list = userinfo_obj.get_following()
        elif l == 'org':
            list = userinfo_obj.followed_organization.all()[::-1]
            print(list)
            grp = True
        
        if request.user.info.skills.all():
            suggested_project = projects.objects.filter(skill_needed__in = request.user.info.skills.all()).distinct().order_by('-created_at')[:5]
        else:
            suggested_project = projects.objects.all()[:5] #For user, with no skill
            
        print(list)
        p = Paginator(list, 20)
        page_number = request.GET.get('page')
        page_obj = p.get_page(page_number)
        context = {
            'userinfo_obj': userinfo_obj,
            'user_list': page_obj,
            'l': l,
            'grp': grp,
            'suggested_project': suggested_project,
            'post_form': post_form,
        }
        
        return render(request, 'myapp/followList.html', context)
    
# Organization
@login_required
def create_organization(request):
    if request.method == "POST":
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            org = form.save(commit=False)
            org.user = request.user
            org.save()
            return redirect('organization_detail', id=org.id)
    else:
        form = OrganizationForm()      
    context  = {'form': form}
    return render(request, 'myapp/create-org.html', context)  
        
@login_required
def explore_organization(request):
    
    type_filter = request.GET.get('type', '').strip()  #string
    industry_filter = request.GET.get('industry', '').strip()   #industry 
    query = request.GET.get('q', '').strip()
    
    filter_conditions = {}
    if industry_filter:
        filter_conditions["industry__id"] = industry_filter
    if type_filter:
        filter_conditions["organization_type"] = type_filter
        
    filtered_org = organization.objects.filter(**filter_conditions).order_by('-created_at')
    
    if query:
        filtered_org = filtered_org.filter(
            Q(name__icontains=query) |  
            Q(organization_type__icontains=query) |  
            Q(industry__name__icontains=query) |  
            Q(description__icontains=query) | 
            Q(location__icontains=query) 
        ).distinct()
        
    applied_filter = bool(type_filter or industry_filter)
    
    if not (applied_filter or query):
        filtered_org = filtered_org[:20]
    
    p = Paginator(filtered_org, 20)
    page_number = request.GET.get("page")
    try:
        page_obj = p.get_page(page_number)  # returns the desired page object
    except PageNotAnInteger:
        page_obj = p.page(1)
    
    result_count = filtered_org.count()
    post_form = PostForm()
    industries = Industry.objects.all().exclude(name__iexact="Other")
    types = organization.get_organization_type_filters
    
    context = {
        'filtered_org': page_obj,
        'post_form': post_form,
        'active_explore': True,
        'result_count': result_count,
        'query': query,
        'applied_filter': applied_filter,
        'types': types,
        'industries': industries
    } 
    return render(request, 'myapp/explore-organization.html', context)

@login_required
def manage_organization(request):
    org_list = request.user.organization.all()
    post_form = PostForm()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_org':
            org_obj = get_object_or_404(organization, id = request.POST.get('org_id'))
            if org_obj.user == request.user:
                org_obj.delete()    
    context = {
        'org_list': org_list,
        'post_form' : post_form,
        'manage_org_page': True
    }
    return render(request, 'myapp/manage_organization.html', context)
        
@login_required
def organization_detail(request, id):
    organization_obj = get_object_or_404(organization, id = id)
    org_post = org_events= link_available = orgForm = editOrg_flag = False
    post_form = PostForm()
    section = request.GET.get('section', 'overview') 
    
    session_key = f'org_viewed_{id}'
    has_viewed = request.session.get(session_key, False)

    if not has_viewed and getattr(organization_obj, 'user', None) != request.user:
        if organization_obj.followers.filter(id=request.user.info.id).exists():
            organization.objects.filter(id=id).update(
                profile_views_followers=F('profile_views_followers') + 1
            )
        else:
            organization.objects.filter(id=id).update(
                profile_views_nonfollowers=F('profile_views_nonfollowers') + 1
            )
        request.session[session_key] = True  # Mark as viewed in this session
    social_links = { 
        'github': organization_obj.github if organization_obj.github else None,
        'linkedin': organization_obj.linkedin if organization_obj.linkedin else None,
        'x-twitter': organization_obj.twitter if organization_obj.twitter else None,
        'discord': organization_obj.discord if organization_obj.discord else None,
        'instagram': organization_obj.instagram if organization_obj.instagram else None
    }
    print(social_links)
    suggested_org = organization.objects.filter(industry=organization_obj.industry, organization_type=organization_obj.organization_type).exclude(Q(id=organization_obj.id) | Q(user=request.user) | Q(followers=request.user.info)).order_by('?')[:5]
    # suggested_org = organization.objects.all()
    if social_links.get('github') or social_links.get('linkedin') or social_links.get('x-twitter') or social_links.get('discord') or social_links.get('instagram'):
            link_available = True
            
    if section == 'posts':
        org_post = post.objects.filter(Organization = organization_obj).order_by('-created_at')
        
    if section == 'events':
        org_events = event.objects.filter(organization = organization_obj).order_by('-created_at')
        
    if organization_obj.user == request.user:
        orgForm = EditOrgForm(instance=organization_obj)
        
    if request.method == "POST" and organization_obj.user == request.user:
        orgForm = EditOrgForm(request.POST, request.FILES, instance=organization_obj)   
        if orgForm.is_valid():
            org_obj = orgForm.save(commit=False)
            cropped_image_data = request.POST.get('croppedImage', '')
            if cropped_image_data:
                try:
                    format, imgstr = cropped_image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    image_data = base64.b64decode(imgstr)
                    file_name = f"{org_obj.name}_profile.{ext}"
                    org_obj.logo = ContentFile(image_data, name=file_name)
                except (ValueError, base64.binascii.Error):
                    orgForm.add_error(None, "Invalid image data. Please upload a valid image.")
                    editOrg_flag = True
            org_obj.save()
            reverse_url = reverse('organization_detail', args=[organization_obj.id])
            return redirect(reverse_url) 
        else:
            print("Validation errors:", orgForm.errors)
            editOrg_flag = True
    context = {
        'organization': organization_obj,
        'section': section,
        'social_links': social_links,
        'link_available': link_available,
        'org_post': org_post,
        'org_events': org_events,
        'color_active' : "bg-black text-white font-bold",
        'suggested_org': suggested_org,
        'post_form': post_form,
        'profile_type': 'organization',
        'EditOrgForm': orgForm,
        'open_editOrg_flag': editOrg_flag
    }
    return render(request, 'myapp/organization-profile.html', context)

@login_required
def org_follow_list(request, org_id):
    org = get_object_or_404(organization, id = org_id)
    list = org.get_followers()
    print(list)
    post_form = PostForm()
    if request.user.info.skills.all():
            suggested_project = projects.objects.filter(skill_needed__in = request.user.info.skills.all()).distinct().order_by('-created_at')[:5]
    else:
        suggested_project = projects.objects.all()[:5] #For user, with no skill
    print(list)
    p = Paginator(list, 25)
    page_number = request.GET.get('page')
    page_obj = p.get_page(page_number)
    context = {
        'org': org,
        'user_list': page_obj,
        'suggested_project': suggested_project,
        'post_form': post_form
    }
    return render(request, 'myapp/org-followlist.html', context)


@login_required
def follow_organization(request, organization_id):
    try:
        org = organization.objects.get(id=organization_id)
        user_info = request.user.info 
        if user_info not in org.followers.all() and user_info != org.user.info:
            org.followers.add(user_info)
            Notification.objects.create(user=org.user.info, sender=user_info, notification_type='follow', organization=org)
            send_notification_email(org.user.info, f'🧑‍💻 {user_info.user.username} Started Following {org.name}')
            return JsonResponse({'status': 'followed', 'action': 'follow', 'message': 'You are now following this organization.', 'followers_count': org.get_followers().count()})
        else:
            return JsonResponse({'status': 'error', 'message': 'You are already following this organization.'}, status=400)
    except org.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Organization not found.'}, status=404)
    
@login_required
def unfollow_organization(request, organization_id):
    try:
        org = organization.objects.get(id=organization_id)
        user_info = request.user.info
        if user_info in org.followers.all() and user_info != org.user.info:
            org.followers.remove(user_info)
            notify_obj = Notification.objects.filter(user=org.user.info, sender=user_info, notification_type='follow', organization=org)
            if notify_obj:
                notify_obj.delete()
            return JsonResponse({'status': 'unfollowed', 'action': 'unfollow', 'message': 'You have unfollowed this organization.', 'followers_count': org.get_followers().count()})
        else:
            return JsonResponse({'status': 'error', 'message': 'You are not following this organization.'}, status=400)
    except org.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Organization not found.'}, status=404)

#explore page:
@login_required
def explore_project(request):
    #filter
    domain_filter = request.GET.get('domain', '').strip()  # ID
    type_filter = request.GET.get('type', '').strip()      # Name
    skill_filter = request.GET.get('skill', '').strip()    # ID
    level_filter = request.GET.get('level', '').strip()    # Name
    query = request.GET.get('q', '').strip()
    
    filter_conditions = {}
    if domain_filter:
        filter_conditions["domain__id"] = domain_filter
    if type_filter:
        filter_conditions["type"] = type_filter
    if level_filter:
        filter_conditions["level"] = level_filter
    if skill_filter:
        filter_conditions["skill_needed__id"] = skill_filter
        
    filter_project = projects.objects.filter(**filter_conditions).order_by('-created_at')
    if query:
        projects_qs = projects.objects.all()
        filter_project = projects_qs.filter(
            Q(title__icontains=query) |  # Partial match on name
            Q(description__icontains=query) |  # Partial match on description
            Q(skill_needed__name__icontains=query) |  # Partial match on skills
            Q(domain__name__icontains=query) | 
            Q(type__icontains = query) |# Partial match on domain
            Q(level__icontains=query)  # Exact match on level (adjust if partial needed)
        ).distinct()
    
    applied_filter = bool(domain_filter or type_filter or skill_filter or level_filter)
    
    if not (applied_filter or query):
        filter_project = filter_project[:200]
    
    #Pagination
    p = Paginator(filter_project, 20)
    page_number = request.GET.get("page")
    post_form = PostForm()
    
    try:
        page_obj = p.get_page(page_number)  # returns the desired page object
    except PageNotAnInteger:
        page_obj = p.page(1)
    
    r = filter_project.count()
    top_domain = Domain.objects.all()[:10]
    top_skills = top_skills_list()
        
    context = {
        'filtered_project': page_obj,
        'total_result': r,
        'top_domains': top_domain,
        'types': ['Open-Source', 'Learning', 'Paid', 'Freelance'],
        'levels': ['Beginner', 'Intermediate', 'Expert'],
        'top_skill': top_skills,
        'applied_filter': applied_filter,
        'post_form': post_form,
        'query': query,
        'active_explore': True
    }
    # print(request.GET)
    return render(request,"myapp/explore-projects.html", context)

@login_required
def explore_dev(request):

    availability_filter = request.GET.get('availability', '').strip()
    status_filter = request.GET.get('status', '').strip()  #ID
    skill_filter = request.GET.get('skill', '').strip()    #ID
    query = request.GET.get('q', '').strip()
    
    filter_conditions = {}
    if availability_filter:
        filter_conditions["availability"] = availability_filter
    if status_filter:
        filter_conditions["status__id"] = status_filter 
    if skill_filter:
        filter_conditions["skills__id"] = skill_filter
    
    filter_dev = userinfo.objects.filter(**filter_conditions).exclude(user=request.user).filter(user__in=verified_user_ids).select_related('user')

    if query:
        filter_dev = filter_dev.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__iexact=query) |
            Q(skills__name__iexact=query) |
            Q(availability__icontains=query) |
            Q(status__name__iexact=query) |
            Q(about_user__icontains=query)
        ).distinct()
    
    applied_filter = bool(availability_filter or status_filter or skill_filter)
    
    if not (applied_filter or query):
        filter_dev = get_explore_users(filter_dev, request)
        
    top_skill= top_skills_list()
    status = user_status.objects.all()
    availability_list = userinfo.get_availability_type_filters
    #Pagination
    p = Paginator(filter_dev, 25)
    page_number = request.GET.get('page')
    try:
        page_obj = p.page(page_number)
    except PageNotAnInteger:
        page_obj = p.page(1)
    r = filter_dev.count()
    post_form = PostForm()
    context = {
        'filter_user': page_obj,
        'top_skill': top_skill,
        'status_list': status,   
        'availability_list': availability_list,
        'total_result': r,  
        'post_form': post_form,  
        'query': query,
        'applied_filter': applied_filter,
        'active_explore_dev': True
    }
    return render(request, 'myapp/explore_dev.html', context)

#Explore event and single page event
@login_required
def explore_events(request):
    #filter
    type_filter = request.GET.get('type', '').strip()  #string
    mode_filter = request.GET.get('mode', '').strip()  #string
    query = request.GET.get('q', '').strip()
    
    filter_conditions = {}
    if type_filter:
        filter_conditions["event_type"] = type_filter
    if mode_filter:
        filter_conditions["mode"] = mode_filter
        
    filtered_events = event.objects.filter(**filter_conditions).order_by('-created_at')
    
    if query:
        filtered_events = filtered_events.filter(
            Q(title__icontains=query) |
            Q(event_type__icontains=query) |
            Q(organization__name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(location__icontains=query) |
            Q(mode__iexact=query)
        ).distinct()
    
    applied_filter = bool(type_filter or mode_filter)
    
    if not (applied_filter or query):
        filtered_events = filtered_events[:100]
        
    p = Paginator(filtered_events, 20)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number)
    except PageNotAnInteger:
        page_obj = p.page(1)
    result_count = filtered_events.count()
    post_form = PostForm()
    modes = event.get_mode_filters()
    types = event.get_event_type_filters()
    context = {
        'post_form': post_form,
        'applied_filter': applied_filter,
        'filtered_event': page_obj,
        'result_count': result_count,
        'query': query,
        'active_explore': True,
        'modes': modes,
        'types': types,
    }
    print(types)
    return render(request, 'myapp/explore-events.html', context)

@login_required
def saved_page(request):
    saved_item  = request.user.info.saved_items
    saved_post = saved_item.posts.all()
    saved_project = saved_item.project.all()
    saved_event = saved_item.events.all()
    post_form = PostForm()
    print(saved_item, request.META.get('HTTP_REFERER', '/'))
    print(saved_event)
    context = {
        'saved_item': saved_item,
        'section': 'posts',
        'post_form': post_form,
        'saved_post': saved_post,
        'saved_project': saved_project,
        'saved_events': saved_event,
    }
    return render(request, 'myapp/saved.html', context)

@login_required
def calendar_page(request):
    post_form = PostForm()
    followed_orgs = request.user.info.followed_organization.all() | request.user.organization.all()
    followed_orgs = followed_orgs.distinct() 
    grouped_events = {}
    projects_qs = False
    
    section = request.GET.get('section', '')
    
    if section == "joined-projects":
        projects_qs = projects.objects.filter(members=request.user.info)[::-1]
    else:
        events_qs = event.objects.filter(organization__in=followed_orgs, start_date__gte=timezone.now()).order_by('start_date')
        # print(events_qs)
        events = list(events_qs)
        for event_date, group in groupby(events, key=lambda e: e.start_date):
            grouped_events[event_date] = list(group)
    context = {
        'grouped_events': grouped_events,
        'post_form': post_form,
        'section': section,
        'joined_projects': projects_qs,
    }
    return render(request, 'myapp/calendar.html', context)

@login_required
def settings_page(request):
    userinfo_obj = request.user.info
    context = {
        'userinfo_obj': userinfo_obj
    }
    return render(request, 'myapp/account_setting.html', context)

@login_required
def toggle_like(request, post_id):
    post_obj = get_object_or_404(post, id = post_id)
    userinfo_obj = request.user.info
    post_owner = post_obj.user if post_obj.user else post_obj.Organization.user.info if post_obj.Organization else None
    print(post_owner)
    if userinfo_obj in post_obj.likes.all():
        post_obj.likes.remove(userinfo_obj)
        liked = False
        if userinfo_obj != post_owner and post_owner:
            Notify_obj = Notification.objects.filter(user=post_owner, sender=userinfo_obj, notification_type="like", post=post_obj)
            print(Notify_obj)
            if Notify_obj:
                Notify_obj.delete()
    else:
        post_obj.likes.add(userinfo_obj)
        liked = True
        if userinfo_obj != post_owner and post_owner:
            notify = Notification.objects.create(user=post_owner, sender=userinfo_obj, notification_type="like", post=post_obj)
            if post_obj.user:
                send_notification_email(post_owner, f'🧑‍💻 {userinfo_obj.user.username} Liked one of your Post 💚')
            elif post_obj.Organization:
                send_notification_email(post_owner, f'🧑‍💻 {userinfo_obj.user.username} {notify.get_notification_type_display()} 💚 on {post_obj.Organization.name}!')
    return JsonResponse({'liked': liked, 'total_likes': post_obj.total_likes()}) 

@login_required
#for saving post
def save_post(request):
    form = PostForm(request.POST, request.FILES)
    action = request.POST.get('action')
    if action == 'user-post':
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.user = request.user.info  # Set current user's profile
            new_post.aspect = request.POST.get("aspect_ratio", "16:9")
            new_post.save()
            redirect_url = reverse('user_profile', args=[request.user.username])
            return redirect(f'{redirect_url}?section=posts')
        else:
            return HttpResponseRedirect('/')
    else:
        org = get_object_or_404(organization, id = action)
        if form.is_valid() and org.user == request.user:
            new_post = form.save(commit=False)
            new_post.Organization = org
            new_post.aspect = request.POST.get("aspect_ratio", "16:9")
            new_post.save()
            redirect_url = reverse('organization_detail', args=[org.id])
            return redirect(f'{redirect_url}?section=posts')
        else:
            return HttpResponseRedirect('/')
        
@login_required
def delete_post(request, post_id):
    post_obj = get_object_or_404(post, id = post_id)
    User = request.user
    if post_obj.user == User.info:
        post_obj.delete()
        return redirect(request.META.get('HTTP_REFERER', '/')) 

    elif post_obj.Organization and post_obj.Organization.user == User:
        post_obj.delete()
        return redirect(request.META.get('HTTP_REFERER', '/')) 
    return HttpResponse("Sorry! You Can't have permission To Delete!...")
    
@login_required
#for saving post comments
def save_comment(request):
    comment_text = request.POST.get('comment')   
    post_id = request.POST.get('post_id')
    Post_obj = get_object_or_404(post, id=post_id)
    post_owner = Post_obj.user if Post_obj.user else Post_obj.Organization.user.info if Post_obj.Organization else None
    comment = post_comments.objects.create(
        Post=Post_obj,
        user=request.user.info,
        content=comment_text
    )
    profile_image_url = comment.user.profile_image.url
    if request.user.info != post_owner:
        Notification.objects.create(user=post_owner, sender=request.user.info, notification_type="comment", post_comment=comment)
        if Post_obj.user:
            send_notification_email(post_owner, f'🧑‍💻 {request.user.username} Commented on one of your post\n\n💬 {comment_text[:50]}...')
        elif Post_obj.Organization:
            send_notification_email(post_owner, f'🧑‍💻 {request.user.username} Commented on {Post_obj.Organization.name}\'s post\n\n💬 {comment_text[:50]}...')
    data = {
        'username': comment.user.user.username,
        'comment': comment.content,
        'comment_id': comment.id,
        'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        'profile_image_url': profile_image_url,
        'comments_count': Post_obj.tot_comments(),
    }
    return JsonResponse(data)

@login_required
def delete_post_comment(request, comment_id):
    if request.method == 'DELETE':
        try:
            comment = post_comments.objects.get(id=comment_id)
            post_id = comment.Post.id
            if comment.user == request.user.info:
                comment.delete()
                comments_count = post_comments.objects.filter(Post__id=post_id).count()
                return JsonResponse({
                    'message': 'Comment deleted',
                    'post_id': post_id,
                    'comments_count': comments_count
                })
            else:
                return
        except post_comments.DoesNotExist:
            return JsonResponse({'error': 'Comment not found'}, status=404)
    else:
        return HttpResponseNotAllowed(['DELETE'])

@login_required
def toggle_post_save(request, post_id):
    post_obj = get_object_or_404(post, id = post_id)
    saved_obj, created = SavedItem.objects.get_or_create(user=request.user.info)
    print(created)
    if post_obj in saved_obj.posts.all():
        saved_obj.posts.remove(post_obj)
        saved = False
    else:
        saved_obj.posts.add(post_obj)
        saved = True
    return JsonResponse({'saved': saved})

@login_required
def delete_data(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == 'project_comment':
            comment_id = request.POST.get("comment_id")
            try:
                comment = project_comment.objects.get(id=comment_id, user=request.user.info)
                Notify_obj = Notification.objects.filter(user=comment.project.creator, sender=request.user.info, project_comment = comment, notification_type="project_comment")
                if Notify_obj:  
                    Notify_obj.delete()
                comment.delete()
                comment_count = comment.project.tot_comments()
                return JsonResponse({"success": True, "comment_count": comment_count})
            except project_comment.DoesNotExist:
                return JsonResponse({"success": False, "error": "Comment not found"})
        elif form_type == 'project_reply':
                reply_id = request.POST.get("comment_id")
                try:
                    comment = project_reply.objects.get(id=reply_id, user=request.user.info)
                    Notify_obj = Notification.objects.filter(user=comment.user, sender=request.user.info, project_reply = comment, notification_type="project_reply")
                # Notification.objects.create(user=r.comment.user, sender=userinfo_obj, project_reply=r, notification_type='project_reply')
                    if Notify_obj:  
                        Notify_obj.delete()
                    comment.delete()
                    comment_count = comment.comment.project.tot_comments()
                    return JsonResponse({"success": True, "comment_count": comment_count})
                except project_reply.DoesNotExist:
                    return JsonResponse({"success": False, "error": "Comment not found"})
        elif form_type == 'event_comment':
            comment_id = request.POST.get("comment_id")
            try:
                comment = event_comment.objects.get(id=comment_id, user=request.user.info)
                comment.delete()
                comment_count = comment.event.tot_comments()
                return JsonResponse({"success": True, "comment_count": comment_count})
            except event_comment.DoesNotExist:
                return JsonResponse({"success": False, "error": "Comment not found"})
        elif form_type == 'event_reply':
            reply_id = request.POST.get("comment_id")
            try:
                comment = event_reply.objects.get(id=reply_id, user=request.user.info)
                comment.delete()
                comment_count = comment.comment.event.tot_comments()
                return JsonResponse({"success": True, "comment_count": comment_count})
            except event_reply.DoesNotExist:
                return JsonResponse({"success": False, "error": "Comment not found"})
        elif form_type == 'delete_exp_obj':
            Id = request.POST.get("exp_id")
            print(Id)
            experience.objects.get(id = Id).delete()
            redirect_url = reverse("user_profile", args=[request.user.username])
            return redirect(f"{redirect_url}?section=info")
        elif form_type == 'user_work':
            Id = request.POST.get('id')
            work_obj = get_object_or_404(user_project, id = Id)
            if work_obj.user == request.user.info:
                work_obj.delete()
                return redirect(f"{reverse('user_profile', args=[request.user.username])}?section=projects")   
            else:
                return HttpResponse("You have No Authority to Delete.")     
    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def delete_account(request, uuid):
    print(True)
    user = request.user
    if uuid == user.info.uuid:
        user.delete()
        logout(request)
    return redirect('/')

@login_required
def logout_view(request):
    logout(request)
    list(messages.get_messages(request))  # Force-clear any leftover messages
    return redirect('account_login')